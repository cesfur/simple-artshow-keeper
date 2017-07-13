function setElementRequiredDisabled(elementId, required, disabled) {
    var element = document.getElementById(elementId);
    if (element != null) {
        element.required = required;
        element.disabled = disabled;
    }
}

function getValue(elementId, defaultValue) {
    var element = document.getElementById(elementId);
    if (element != null) {
        return element.value;
    }
    else {
        return defaultValue;
    }
}

function isValueChanged(elementId, oldValue) {
    var value = getValue(elementId, null);
    return value != null && String(value) != String(oldValue);
}

function updateElements() {
    var forSaleElement = document.getElementById("forSale");
    if (forSaleElement != null) {
        var forSale = forSaleElement.checked;
        setElementRequiredDisabled("initialAmount", forSale, !forSale);
        setElementRequiredDisabled("charity", forSale, !forSale);
    }
}

function onUpdateClick() {
    var sensitive = false;

    var state = getValue("state", "")
    if (state != startingValues.state) {
        sensitive |=  amountSensitiveStates[state] || amountSensitiveStates[startingValues.state];
    }
    if (amountSensitiveStates[state]) {
        sensitive |= getValue("amount", 0) != startingValues.amount
            || getValue("charity", 0) != startingValues.charity
            || getValue("buyer", 0) != startingValues.buyer;
    }

    return !sensitive || window.confirm(promptReconcialitionChange);
}

function onCancelClick() {
    var changed = isValueChanged("owner", startingValues.owner)
        || isValueChanged("author", startingValues.author)
        || isValueChanged("title", startingValues.title)
        || isValueChanged("state", startingValues.state)
        || isValueChanged("medium", startingValues.medium)
        || isValueChanged("initialAmount", startingValues.initialAmount)
        || isValueChanged("amount", startingValues.amount)
        || isValueChanged("charity", startingValues.charity)
        || isValueChanged("buyer", startingValues.buyer)
        || isValueChanged("note", startingValues.note)
    return !changed || window.confirm(promptUpdateLost);
}
