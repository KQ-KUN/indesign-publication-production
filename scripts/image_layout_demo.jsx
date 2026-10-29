#target "InDesign"
#include "image_layout_host.jsx"
#include "../.artifacts/image-layout/request.jsx"
(function () {
    var request = IMAGE_LAYOUT_DEMO_REQUEST, context = {stage:"create-document"}, doc = null;
    var helper = PublicationImageHost, oldInteraction = app.scriptPreferences.userInteractionLevel, oldUnit = app.scriptPreferences.measurementUnit;
    var pdfKeys = ["pageRange","viewPDF","exportReaderSpreads","cropMarks","bleedMarks","registrationMarks",
        "colorBars","pageInformationMarks","useDocumentBleedWithPDF"], oldPdf = {}, pk;
    for (pk = 0; pk < pdfKeys.length; pk += 1) { oldPdf[pdfKeys[pk]] = app.pdfExportPreferences[pdfKeys[pk]]; }
    function focus() {
        if (doc && doc.isValid && doc.pages.length > 0 && app.layoutWindows.length > 0) {
            app.activeWindow.activePage = doc.pages[0];
        }
    }
    try {
        app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;
        app.scriptPreferences.measurementUnit = MeasurementUnits.MILLIMETERS;
        doc = app.documents.add(); doc.documentPreferences.facingPages = false;
        doc.documentPreferences.pageWidth = "185mm"; doc.documentPreferences.pageHeight = "260mm";
        doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.MILLIMETERS;
        doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.MILLIMETERS;
        doc.viewPreferences.rulerOrigin = RulerOrigin.PAGE_ORIGIN; doc.zeroPoint = [0,0];
        doc.insertLabel("image_layout_demo_run",request.run_id);
        var font = app.fonts.itemByName("Source Han Sans SC\tRegular");
        if (!font || !font.isValid) { font = app.fonts.itemByName("SimSun\tRegular"); }
        helper.check(font && font.isValid, "Demo requires installed Source Han Sans SC or SimSun for bilingual captions");
        var reports = [], units = [], i, page, heading, note, sample;
        for (i = 0; i < request.cases.length; i += 1) {
            sample = request.cases[i];
            if (i % 2 === 0) {
                page = i === 0 ? doc.pages[0] : doc.pages.add();
                heading = page.textFrames.add(); heading.geometricBounds = [8,16,17,169];
                heading.contents = "Column image geometry / native proof " + (Math.floor(i/2)+1);
                heading.parentStory.appliedFont = font; heading.parentStory.pointSize = "12pt"; heading.parentStory.leading = "14pt";
            }
            context.stage = "place-case"; context.case_id = sample.id;
            heading = page.textFrames.add(); heading.geometricBounds = [22,sample.plan.column.x,34,sample.plan.column.x+73];
            heading.contents = sample.id + "  " + sample.title;
            heading.parentStory.appliedFont = font; heading.parentStory.pointSize = "9pt"; heading.parentStory.leading = "11pt";
            units.push(helper.place(doc,page,sample.plan,context,font));
            note = page.textFrames.add(); note.geometricBounds = [166,sample.plan.column.x,222,sample.plan.column.x+73];
            note.contents = sample.note; note.parentStory.appliedFont = font; note.parentStory.pointSize = "9pt"; note.parentStory.leading = "13pt";
        }
        context.stage = "read-native-geometry"; doc.recompose();
        for (i = 0; i < units.length; i += 1) { reports.push({id:request.cases[i].id,actual:helper.snapshot(units[i])}); }
        var frames = doc.textFrames.everyItem().getElements();
        for (i = 0; i < frames.length; i += 1) { helper.check(!frames[i].overflows,"Overset demo text frame " + i); }
        var fonts = doc.fonts.everyItem().getElements();
        for (i = 0; i < fonts.length; i += 1) { helper.check(fonts[i].status === FontStatus.INSTALLED,"Missing font"); }
        context.stage = "export-pdf"; doc.save(File(request.indd));
        app.pdfExportPreferences.pageRange = PageRange.ALL_PAGES;
        app.pdfExportPreferences.viewPDF = false; app.pdfExportPreferences.exportReaderSpreads = false;
        app.pdfExportPreferences.cropMarks = false; app.pdfExportPreferences.bleedMarks = false;
        app.pdfExportPreferences.registrationMarks = false; app.pdfExportPreferences.colorBars = false;
        app.pdfExportPreferences.pageInformationMarks = false; app.pdfExportPreferences.useDocumentBleedWithPDF = false;
        doc.exportFile(ExportFormat.PDF_TYPE,File(request.pdf),false); focus();
        helper.write(request.report,{status:"PASS",run_id:request.run_id,native_version:app.version,
            document_pages:doc.pages.length,overset:false,cases:reports,focus_page:doc.pages[0].name});
        return "PASS image geometry demo;run=" + request.run_id + ";pages=" + doc.pages.length;
    } catch (e) {
        helper.write(request.report,{status:"FAIL",run_id:request.run_id,stage:context.stage,context:context,
            name:e.name,message:e.message,file:e.fileName,line:e.line,source:e.source,stack:$.stack});
        return "FAIL image geometry demo;stage=" + context.stage + ";message=" + e.message + ";line=" + e.line;
    } finally {
        focus(); app.scriptPreferences.userInteractionLevel = oldInteraction; app.scriptPreferences.measurementUnit = oldUnit;
        for (pk = 0; pk < pdfKeys.length; pk += 1) { app.pdfExportPreferences[pdfKeys[pk]] = oldPdf[pdfKeys[pk]]; }
    }
}());
