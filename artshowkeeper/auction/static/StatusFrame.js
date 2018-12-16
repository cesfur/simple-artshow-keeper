function createHttpRequest()
{
    var activexmodes=["Msxml2.XMLHTTP", "Microsoft.XMLHTTP"]
    if (window.ActiveXObject)
    { // Test for support for ActiveXObject in IE first (XMLHttpRequest in IE7 is broken)
        for (var i = 0; i < activexmodes.length; i++)
        {
            try
            {
                return new ActiveXObject(activexmodes[i]);
            }
            catch(e)
            {
            }
        }
        
        return null;
    }
    else if (window.XMLHttpRequest)
    { // Mozilla, Safari etc.
        return new XMLHttpRequest();
    }
    else
    {
        return null;
    }
}

function getFrameElement(elementId)
{
    var frame = document.getElementById("frame");
	if (frame == null)
	{
        console.error("getFrameElement: Frame not found.");
		return null;
	}
	else
	{
		var element = frame.getElementById(elementId)
		if (element == null)
		{
			console.error("getFrameElement: Element '" + elementId + "' not found.");
			return null;
		}
		else
		{
			return element;
		}
	}
}

function getValueOrNull(xmlDoc, root, xpath)
{
    var value = null;
    if (xmlDoc != null && root != null)
    {
        var node = xmlDoc.evaluate(xpath, root, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        if (node != null && node.singleNodeValue != null)
        {
            value = node.singleNodeValue.textContent;
        }
    }
    return value;
}

function getTagOrNull(root, tagName)
{
    var tag = null;
    if (root != null)
    {
        var tags = root.getElementsByTagName(tagName)
        if (tags.length > 0)
        {
            tag = tags[0];
        }
    }
    return tag;
}

function setFrameElementText(elementId, textValue)
{
    var element = document.getElementById(elementId);
    if (element == null) {
        console.error("setElementText: Cannot update an element '" + elementId + "' because element is not defined.");
    } else {
        if (textValue == null) {
            textValue = "";
        }
        if (element.textContent != textValue) {
            element.textContent = textValue;
        }
    }
}

function setItemImage(itemImageURL) {
    var itemImageVisible = false;
    var itemImage = document.getElementById("image_image");
    if (itemImage != null) {
        if (itemImageURL != null) {
            if (itemImageURL != itemImage.getAttribute('src')) {
                itemImage.setAttribute('src', itemImageURL);
            }
            itemImageVisible = true;
        } else {
            itemImage.setAttribute('src', '');
        }
        itemImage.hidden = !itemImageVisible;
    }
}

function setScreenClass(value) {
    element = document.getElementsByTagName("body")[0];
    if (element != null) {
        if (!element.hasAttribute("class") || element.getAttribute("class") != value) {
            element.setAttribute("class", value);
        }
    }
}

function processResponse(xmlDoc)
{
    try
    {
        if (xmlDoc != null)
        {
            var tagAuction = getTagOrNull(xmlDoc, "Auction");

            //class
            if (getValueOrNull(xmlDoc, tagAuction, "//Item/Title") == null || getValueOrNull(xmlDoc, tagAuction, "//Item/Author") == null) {
                setScreenClass("summaryOnly")
            } else if (getValueOrNull(xmlDoc, tagAuction, "//Item/Image") == null) {
                setScreenClass("itemSummary")
            } else {           
                setScreenClass("itemImageSummary")
            }

            //item
            setFrameElementText("item_title", getValueOrNull(xmlDoc, tagAuction, "//Item/Title"));
            setFrameElementText("item_author", getValueOrNull(xmlDoc, tagAuction, "//Item/Author"));
            setFrameElementText("item_medium", getValueOrNull(xmlDoc, tagAuction, "//Item/Medium"));
            setFrameElementText("item_amount_1", getValueOrNull(xmlDoc, tagAuction, "//Item/Amount/FormattedValue[1]"));
            setFrameElementText("item_amount_2", getValueOrNull(xmlDoc, tagAuction, "//Item/Amount/FormattedValue[2]"));
            setFrameElementText("item_amount_3", getValueOrNull(xmlDoc, tagAuction, "//Item/Amount/FormattedValue[3]"));
            setFrameElementText("item_charity", getValueOrNull(xmlDoc, tagAuction, "//Item/Charity"));
            setItemImage(getValueOrNull(xmlDoc, tagAuction, "//Item/Image"));

            //charity
            setFrameElementText("charity_1", getValueOrNull(xmlDoc, tagAuction, "//Charity/FormattedValue[1]"));
            setFrameElementText("charity_2", getValueOrNull(xmlDoc, tagAuction, "//Charity/FormattedValue[2]"));
            setFrameElementText("charity_3", getValueOrNull(xmlDoc, tagAuction, "//Charity/FormattedValue[3]"));
        }
    }
    catch(e)
    {
        console.error("processResponse: Failed to process a response with an exception: " + e);
    }
}

function onRefresh()
{
    var request = createHttpRequest()
    request.onreadystatechange = function()
    {
        if ((request.readyState == 4) && (request.status == 200))
        {
            processResponse(request.responseXML);
        }
    }
    var url = document.getElementById("statusURL").innerText;
    request.open("GET", url, true)
    request.send(null)
}

function isBrowserValid()
{
    var request = createHttpRequest()
    if (request == null)
    {    
        console.error("isBrowserValid: Cannot create HTTP request.");
        return false;
    }
    return true;
}

function start()
{
    if (isBrowserValid())
    {
        setInterval(onRefresh, 1500);
    }
    else
    {
        alert("Browser not supported.");
    }
}

window.onload = start;
