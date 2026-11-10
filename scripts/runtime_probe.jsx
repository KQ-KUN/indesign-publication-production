#target "indesign"
(function () {
    // Read-only: does not create, save, close, or alter any document/preference.
    return "PASS InDesign " + app.version + ";path=" + app.fullName.fsName +
        ";documents=" + app.documents.length + ";modal=" + String(app.modalState);
}());
