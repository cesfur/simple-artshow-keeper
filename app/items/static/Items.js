/* update item to close */
var updateItemToClose = new function () {
    this.setFormAction = function(button) {
        if (button) {
            document.getElementById('action').value = button.id;
        } else {
            document.getElementById('action').value = '';
        }
        return true;
    }

    this.validate = function() {
        var valid = true;
        if (document.getElementById('action').value == 'auction') {
            var imageElement = document.getElementById('imageFile');
            if (imageElement && document.createEvent) {
                var evt = document.createEvent("MouseEvents");
                evt.initEvent("click", true, false);
                imageElement.dispatchEvent(evt);
            }
            valid = imageElement.value || confirm(artshow.getMessage('messageClosedWithoutImage'));
        }
        return valid;
    }

    this.main = function () {
        this.setFormAction(null);
    }
}
