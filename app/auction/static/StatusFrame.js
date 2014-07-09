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

function getFrameDocument()
{
    var frameDoc = null;
    var embedingElement = document.getElementById("id_frame");

    if (embedingElement == null)
    {
        console.error("getFrameDocument: Element 'id_frame' not found.");
    }    
    else if (embedingElement.contentDocument) 
    {
        frameDoc = embedingElement.contentDocument;
    } 
    else 
    {
        try
        {
            frameDoc = embedingElement.getSVGDocument();
        }
        catch(e)
        {
            console.error("getFrameDocument: Element 'id_frame' does not contain an SVG document.");
        }
    }
    
    return frameDoc;
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

function getFormattedCurrencyOrNull(xmlDoc, root, xpath, currency)
{
    var value = getValueOrNull(xmlDoc, root, xpath);
    if (value != null)
    {
        switch(currency)
        {
        case g_primaryCurrencyCode:
            return g_primaryCurrencyPrefix + Math.round(value) + g_primaryCurrencySuffix;
        case g_secondaryCurrencyCode:
            return g_secondaryCurrencyPrefix + Math.round(value) + g_secondaryCurrencySuffix;
        default:
            return null;
        }
    }
    else
    {
        return null;
    }
}

function setElementText(ownerDoc, elementId, textValue)
{
    if (ownerDoc == null)
    {
        console.error("setElementText: Cannot update an element '" + elementId + "' because owner is null.");
    }
    else
    {
        if (textValue == null)
        {
            textValue = "";
        }

        var element = ownerDoc.getElementById(elementId);
        if (element != null)
        {
            if (element.hasChildNodes())
            {
                element = element.childNodes[0];
            }
            element.textContent = textValue;
        }
        else
        {
            console.error("setElementText: Element '" + elementId + "' not found.");
        }
    }
}

function setFrameElementText(elementId, textValue)
{
    setElementText(getFrameDocument(), elementId, textValue);
}

function processResponse(xmlDoc)
{
    try
    {
        if (xmlDoc != null)
        {
            var tagAuction = getTagOrNull(xmlDoc, "Auction");

             //item
            setFrameElementText("item_title", getValueOrNull(xmlDoc, tagAuction, "Item/Title"));
            setFrameElementText("item_author", getValueOrNull(xmlDoc, tagAuction, "Item/Author"));
            setFrameElementText("item_amount_1", getValueOrNull(xmlDoc, tagAuction, "Item/Amount/FormattedValue[1]"));
            setFrameElementText("item_amount_2", getValueOrNull(xmlDoc, tagAuction, "Item/Amount/FormattedValue[2]"));
            setFrameElementText("item_amount_3", getValueOrNull(xmlDoc, tagAuction, "Item/Amount/FormattedValue[3]"));

            //charity
            setFrameElementText("charity_1", getValueOrNull(xmlDoc, tagAuction, "Charity/FormattedValue[1]"));
            setFrameElementText("charity_2", getValueOrNull(xmlDoc, tagAuction, "Charity/FormattedValue[2]"));
            setFrameElementText("charity_3", getValueOrNull(xmlDoc, tagAuction, "Charity/FormattedValue[3]"));
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
    request.open("GET", g_getStatusUrl, true)
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

function onLoad()
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
