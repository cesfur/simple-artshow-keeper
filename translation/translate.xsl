<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:svg="http://www.w3.org/2000/svg">
    <xsl:output method="html" encoding="utf-8"/>

    <xsl:strip-space elements="*" />

    <xsl:variable name="messages" select="document(/html/head/meta[@name='messages']/@content)/messages"/>
    
    <xsl:template match="//span[@id]">
        <xsl:choose>
            <xsl:when test="$messages/msg[@id=current()/@id]">
                <xsl:value-of select="$messages/msg[@id=current()/@id]" disable-output-escaping="yes"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="current()" disable-output-escaping="yes"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <xsl:template match="node() | @*">
        <xsl:copy>
            <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
