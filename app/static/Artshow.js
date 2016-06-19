/* Global functions */
function setInputFocus(elementName) {
    document.getElementsByName(elementName)[0].focus();
}

var artshow = new function () {
    this.getGetElementByName = function(name) {
        var elements = document.getElementsByName(name);
        if (elements.length > 0) {
            return elements[0];
        } else {
            return false;
        }
    }

    this.enable = function (id, enable) {
        if (document.getElementById(id)) {
            return document.getElementById(id).disabled = !enable;
        } if (this.getGetElementByName(id)) {
            return this.getGetElementByName(id).disabled = !enable;
        }
    }

    this.setClass = function (id, className) {
        var element = document.getElementById(id);
        if (!element) {
            element = this.getGetElementByName(id);
        }
        if (element) {
            if (!element.hasAttribute("class") || element.getAttribute("class") != className) {
                element.setAttribute("class", className);
            }
        }
    }

    this.getMessage = function(messageID) {
        if (document.getElementById(messageID)) {
            return document.getElementById(messageID).innerHTML;
        } else {
            return messageID;
        }
    }

    this.showErrorMessage = function(messageID) {
        this.showError(this.getMessage(messageID));
    }

    this.showError = function(message) {
        alert(message);
    }

    this.printAndSubmit = function(formID) {
        window.print();
        document.getElementById(formID).submit();
    }
}
