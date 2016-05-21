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
}

/* Edit item image */
var editItemImage = new function () {
    var cameras = null;
    var selectedCameraID = null;
    var currentCameraID = null;
    var currentCameraStream = null;

    var captureImage = function () {
        if (currentCameraStream) {
            artshow.enable("ImageSave", false);

            var video = document.getElementById("imageLive");
            var canvas = document.getElementById("imageSnapshot");
            var videoWidth = video.videoWidth;
            var videoHeight = video.videoHeight;

            if (canvas.width !== videoWidth || canvas.height !== videoHeight) {
                canvas.width = videoWidth;
                canvas.height = videoHeight;
            }
            var context = canvas.getContext("2d");
            context.drawImage(video, 0, 0, videoWidth, videoHeight);

            artshow.enable("ImageSave", true);
        }
    }

    var handleMediaError = function(error) {
        if (error.name.indexOf("NotFoundError") >= 0) {
            artshow.showErrorMessage("messageNoCamera");
        } else if (error.name.indexOf("PermissionDeniedError") >= 0) {
            artshow.showErrorMessage("messageCameraNotAllowed");
        } else {
            artshow.showErrorMessage(artshow.getMessage("messageUnknownError") + " " + error.name);
        }
    }

    var closeCamera = function() {
        if (currentCameraID !== null) {
            var video = document.getElementById("imageLive");
            if (typeof(video.srcObject) !== 'undefined') {
                video.srcObject = null;
            }
            video.src = null;

            document.getElementById("imageLive").removeEventListener("click", captureImage);

            if (currentCameraStream) {
                var videoTracks = currentCameraStream.getVideoTracks();
                videoTracks[0].stop();
                currentCameraStream = null;
            }

            currentCameraID = null;
        }
    }

    var openCamera = function(cameraID) {
        closeCamera();

        var video = document.getElementById("imageLive");

        selectedCameraID = cameraID;
        navigator.mediaDevices.getUserMedia({
            video: {
                width: { min: video.offsetParent.offsetWidth },
                height: { min: video.offsetParent.offsetHeight },
                deviceId: { exact: selectedCameraID }
            }
        }).then(initializeCameraStream).catch(handleMediaError);
    };

    var initializeCameraStream = function (stream) {
        currentCameraStream = stream;
        currentCameraID = selectedCameraID;

        var video = document.getElementById("imageLive");
        video.srcObject = currentCameraStream;

        if (video.paused) {
            video.play();
        }

        document.getElementById("imageLive").addEventListener("click", captureImage, false);
    };

    var deviceChanged = function() {
        navigator.mediaDevices.removeEventListener('devicechange', deviceChanged);
        cameras = [];
        navigator.mediaDevices.enumerateDevices().then(devicesEnumerated).catch(handleMediaError);
    }
        
    var devicesEnumerated = function(devices) {
        cameras = [];
        for (var i = 0; i < devices.length; i++) {
            if (devices[i].kind === "videoinput") {
                cameras[cameras.length] = devices[i].deviceId;
            }
        }

        if (cameras.length == 0) {
            artshow.showErrorMessage("messageNoCamera");
        } else {
            openCamera(cameras[0]);
        }

        navigator.mediaDevices.addEventListener("devicechange", deviceChanged);
    }

    this.saveImage = function () {
        var canvas = document.getElementById("imageSnapshot");
        var canvasData = canvas.toDataURL("image/jpeg", 85);
        artshow.getGetElementByName("ImageData").value = canvasData;
        return true;
    }

    this.main = function () {
        artshow.enable("ImageSave", false);
        artshow.enable("ImageDelete", false);
        if (!navigator.getUserMedia) {
            showErrorMessage("messageNotSuported");
        } else {
            navigator.mediaDevices.enumerateDevices().then(devicesEnumerated).catch(handleMediaError);
        }
    }
}