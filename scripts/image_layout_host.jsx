/* Include after calculating a plan with image_layout.py. Caller sets page-local mm. */
var PublicationImageHost = {
    check: function (value, message) { if (!value) { throw new Error(message); } },
    at: function (collection, index) {
        if (!collection || collection.length <= index) { return null; }
        var item = collection[index];
        return item && item.getElements ? item.getElements()[0] : item;
    },
    json: function (value) {
        var self = this, i, parts = [], key;
        if (value === null || typeof value === "undefined") { return "null"; }
        if (typeof value === "number") { this.check(isFinite(value), "Nonfinite JSON number"); return String(value); }
        if (typeof value === "boolean") { return value ? "true" : "false"; }
        if (typeof value === "string") {
            return '"' + value.replace(/[\\"\u0000-\u001f]/g, function (c) {
                var hex = c.charCodeAt(0).toString(16);
                return "\\u" + ("0000" + hex).substr(hex.length);
            }) + '"';
        }
        if (value instanceof Array) {
            for (i = 0; i < value.length; i += 1) { parts.push(self.json(value[i])); }
            return "[" + parts.join(",") + "]";
        }
        for (key in value) { if (value.hasOwnProperty(key)) { parts.push(self.json(key) + ":" + self.json(value[key])); } }
        return "{" + parts.join(",") + "}";
    },
    write: function (path, value) {
        var file = File(path); file.encoding = "UTF-8";
        this.check(file.open("w"), "Cannot write " + path); file.write(this.json(value)); file.close();
    },
    box: function (item, page) {
        this.check(item && item.isValid !== false && page && page.isValid !== false, "Invalid native geometry object");
        var b = item.geometricBounds, pb = page.bounds;
        this.check(b && b.length === 4 && pb && pb.length === 4, "Missing native bounds");
        return {x:Number(b[1])-Number(pb[1]),y:Number(b[0])-Number(pb[0]),
            width:Number(b[3])-Number(b[1]),height:Number(b[2])-Number(b[0])};
    },
    bounds: function (box, page) {
        var pb = page.bounds;
        return [Number(pb[0])+box.y, Number(pb[1])+box.x, Number(pb[0])+box.y+box.height, Number(pb[1])+box.x+box.width];
    },
    place: function (doc, page, plan, context, font) {
        this.check(doc.viewPreferences.horizontalMeasurementUnits === MeasurementUnits.MILLIMETERS &&
            doc.viewPreferences.verticalMeasurementUnits === MeasurementUnits.MILLIMETERS &&
            app.scriptPreferences.measurementUnit === MeasurementUnits.MILLIMETERS, "Image adapter requires explicit script/page mm");
        var rects = [], captions = [], i, f, rect, placed, graphic, frame;
        for (i = 0; i < plan.frames.length; i += 1) {
            f = plan.frames[i]; context.stage = "place-image"; context.image_id = f.image_id;
            this.check(File(f.source.path).exists, "Missing linked source " + f.source.path);
            rect = page.rectangles.add(); rect.geometricBounds = this.bounds(f,page);
            rect.strokeWeight = 0; rect.strokeColor = this.at(doc.swatches,0); rect.fillColor = this.at(doc.swatches,0);
            rect.insertLabel("image_layout_id", f.image_id);
            placed = rect.place(File(f.source.path)); graphic = this.at(placed,0);
            this.check(graphic && graphic.isValid !== false, "Image " + f.image_id + ": place returned no graphic");
            if (f.fit_mode === "COVER") { rect.fit(FitOptions.FILL_PROPORTIONALLY); }
            else if (f.fit_mode === "CONTAIN") { rect.fit(FitOptions.PROPORTIONALLY); }
            else if (f.fit_mode === "STRETCH") { rect.fit(FitOptions.CONTENT_TO_FRAME); }
            else { throw new Error("Unsupported fit mode " + f.fit_mode); }
            rect.fit(FitOptions.CENTER_CONTENT); rects.push(rect);
        }
        for (i = 0; i < plan.captions.length; i += 1) {
            f = plan.captions[i]; frame = page.textFrames.add(); frame.geometricBounds = this.bounds(f,page);
            frame.contents = f.text; frame.parentStory.appliedFont = font;
            frame.parentStory.pointSize = "8pt"; frame.parentStory.leading = "10pt";
            frame.textFramePreferences.insetSpacing = [0,0,0,0];
            frame.insertLabel("image_layout_caption_ids", f.image_ids.join("|")); captions.push(frame);
        }
        doc.recompose(); return {rects:rects,captions:captions};
    },
    snapshot: function (unit) {
        var items = [], captions = [], i, rect, page, graphic, link, frame, text, ids;
        for (i = 0; i < unit.rects.length; i += 1) {
            rect = this.at(unit.rects,i); this.check(rect && rect.isValid !== false, "Lost placed rectangle " + i);
            page = rect.parentPage; this.check(page && page.isValid !== false, "Image has no actual document page");
            graphic = this.at(rect.graphics,0); this.check(graphic, "Rectangle lost graphic " + i);
            link = graphic.itemLink; this.check(link && link.isValid !== false, "Graphic has no link " + i);
            items.push({image_id:rect.extractLabel("image_layout_id"),frame:this.box(rect,page),graphic:this.box(graphic,page),
                page_id:page.id,source_path:link.filePath,link_missing:link.status !== LinkStatus.NORMAL,
                rotation:Number(graphic.rotationAngle),shear:Number(graphic.shearAngle),effective_ppi:graphic.effectivePpi});
        }
        for (i = 0; i < unit.captions.length; i += 1) {
            frame = this.at(unit.captions,i); page = frame.parentPage; this.check(page, "Caption has no page");
            text = String(frame.parentStory.contents); if (text.charAt(text.length-1) === "\r") { text = text.substr(0,text.length-1); }
            ids = frame.extractLabel("image_layout_caption_ids").split("|");
            captions.push({frame:this.box(frame,page),text:text,image_ids:ids,overflows:frame.overflows,page_id:page.id,font_size_pt:Number(frame.parentStory.pointSize)*72/25.4});
        }
        return {origin:"InDesign_DOM",units:"mm",items:items,captions:captions,anchored:false};
    }
};
