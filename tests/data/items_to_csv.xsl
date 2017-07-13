<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:svg="http://www.w3.org/2000/svg">
<xsl:output method="text" encoding="utf-8" indent="no"/>

<xsl:strip-space elements="*" />

<xsl:variable name='newline'><xsl:text>
</xsl:text></xsl:variable>

<xsl:template match="//Item">
    <xsl:value-of select="Code"/>
    <xsl:text>|</xsl:text>
    <xsl:value-of select="Owner"/>
    <xsl:text>|</xsl:text>
    <xsl:value-of select="State"/>
    <xsl:text>|</xsl:text>
    <xsl:value-of select="InitialAmount"/>
    <xsl:text>|</xsl:text>
    <xsl:value-of select="Buyer"/>
    <xsl:text>|</xsl:text>
    <xsl:value-of select="Amount"/>
    <xsl:text>|</xsl:text>
    <xsl:value-of select="Charity"/>
    <xsl:text>|</xsl:text>
    <xsl:value-of select="AmountInAuction"/>
    <xsl:value-of select="$newline"/>
</xsl:template>

<xsl:template match="/">
    <xsl:text>Code|Owner|State|InitialAmount|Buyer|Amount|Charity|AmountInAuction</xsl:text>
    <xsl:value-of select="$newline"/>
    <xsl:apply-templates/>
</xsl:template>

</xsl:stylesheet>
