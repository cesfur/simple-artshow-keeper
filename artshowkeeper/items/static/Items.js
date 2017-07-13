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

    this.enableInput = function (enable) {
        artshow.enable('notsold', enable);
        artshow.enable('sold', enable);
        artshow.enable('auction', enable);
        artshow.enable('cancel', enable);
    }

    this.validate = function() {
        var valid = true;
        if (document.getElementById('action').value == 'auction') {
            this.enableInput(false);
            var imageElement = document.getElementById('imageFile');
            if (imageElement && document.createEvent) {
                var evt = document.createEvent("MouseEvents");
                evt.initEvent("click", true, false);
                imageElement.dispatchEvent(evt);
            }
            if (imageElement.value || confirm(artshow.getMessage('messageClosedWithoutImage'))) {
                valid = true;
            } else {
                this.enableInput(true);
                valid = false;
            }

        }
        return valid;
    }

    this.main = function () {
        this.setFormAction(null);
    }
}
