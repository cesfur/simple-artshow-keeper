<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xhtml="http://www.w3.org/1999/xhtml"
                xmlns:artshow="http://artshow"
                xmlns="http://www.w3.org/1999/xhtml">
    <xsl:output method="html" encoding="utf-8"/>

    <xsl:strip-space elements="*" />

    <xsl:variable
            name="translation"
            select="document(/xhtml:html/xhtml:head/xhtml:meta[@name='translation']/@content)/artshow:translation"/>

    <xsl:template name="translate">
        <xsl:param name="id" />
        <xsl:choose>
            <xsl:when test="$translation/artshow:msg[@id=$id]">
                <xsl:value-of select="$translation/artshow:msg[@id=$id]" disable-output-escaping="yes"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$id" disable-output-escaping="yes"/>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>
    
    <xsl:template match="@value[starts-with(., '__')]">
        <xsl:attribute name="value">
            <xsl:call-template name="translate">
                <xsl:with-param name="id">
                    <xsl:value-of select="substring-after(current(), '__')"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:attribute>
    </xsl:template>

    <xsl:template match="node()[starts-with(., '__')]">
        <xsl:copy>
            <xsl:call-template name="translate">
                <xsl:with-param name="id">
                    <xsl:value-of select="substring-after(current(), '__')"/>
                </xsl:with-param>
            </xsl:call-template>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="node() | @*">
        <xsl:copy>
            <xsl:apply-templates select="node() | @*" />
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
