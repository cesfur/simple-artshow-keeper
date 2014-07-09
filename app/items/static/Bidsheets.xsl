<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:svg="http://www.w3.org/2000/svg">
    <xsl:output method="html" encoding="utf-8"/>

    <xsl:strip-space elements="*" />
    
    <xsl:variable name="bidsheetPerPage" select="//Render/BedsheetsPerPage"/>
    <xsl:variable name="bidsheet" select="//Render/BidsheetFrame[@type='forSale']"/>
    <xsl:variable name="bidsheetNoSale" select="//Render/BidsheetFrame[@type='noSale']"/>

    <xsl:variable name="inputDocument" select="/"/>

    <xsl:template match="/">
        <html>
            <head>
                <link rel="stylesheet" type="text/css">
                    <xsl:attribute name="href">
                        <xsl:value-of select="//UI/StyleSheet"/>
                    </xsl:attribute>
                </link>
                <link rel="stylesheet" type="text/css">
                    <xsl:attribute name="href">
                        <xsl:value-of select="//Render/StyleSheet"/>
                    </xsl:attribute>
                </link>

                <title>
                    <xsl:value-of select="//UI/Title"/>
                </title>
                <script>
                    function printAndSubmit()
                    {
                    window.print();
                    document.getElementById("printControl").submit();
                    }
                </script>
            </head>
            <body>
                <h1 class="notPrintable">
                    <xsl:value-of select="//UI/Header"/>
                </h1>
                <xsl:call-template name="UIControl"/>
                <xsl:apply-templates select="Bidsheets/Item"/>
            </body>
        </html>
    </xsl:template>

    <!-- Controls -->
    <xsl:template name="UIControl">
        <form id="printControl" class="main notPrintable">
            <xsl:attribute name="action">
                <xsl:value-of select="//UI/Button[@action='print']/@target"/>
            </xsl:attribute>
            <input class="action" type="submit">
                <xsl:attribute name="value">
                    <xsl:value-of select="//UI/Button[@action='cancel']"/>
                </xsl:attribute>
                <xsl:attribute name="formaction">
                    <xsl:value-of select="//UI/Button[@action='cancel']/@target"/>
                </xsl:attribute>
            </input>
            <input class="action" type="button" onclick="printAndSubmit()">
                <xsl:attribute name="value">
                    <xsl:value-of select="//UI/Button[@action='print']"/>
                </xsl:attribute>
            </input>
        </form>
    </xsl:template>

    <!-- Item -->
    <xsl:template match="Item">
        <div class="bidsheet">
            <xsl:choose>
                <xsl:when test="Amount">
                    <xsl:apply-templates select="document($bidsheet)/svg:svg">
                        <xsl:with-param name="item" select="." />
                    </xsl:apply-templates>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:apply-templates select="document($bidsheetNoSale)/svg:svg">
                        <xsl:with-param name="item" select="." />
                    </xsl:apply-templates>
                </xsl:otherwise>
            </xsl:choose>
        </div>
        <xsl:choose>
            <xsl:when test="(position() mod $bidsheetPerPage) = 0">
                <div class="pageBreak"></div>
            </xsl:when>
            <xsl:otherwise>
                <div class="manualCut"></div>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>

    <!-- Element bindings -->
    <xsl:template match="svg:text[@id='item_code']/svg:tspan | svg:text[(@id='item_code') and (count(child::*) = 0)]">
        <xsl:param name="item" />
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <xsl:value-of select="$item/Code"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="svg:text[@id='item_title']/svg:tspan | svg:text[(@id='item_title') and (count(child::*) = 0)]">
        <xsl:param name="item" />
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <xsl:value-of select="$item/Title"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="svg:text[@id='item_author']/svg:tspan | svg:text[(@id='item_author') and (count(child::*) = 0)]">
        <xsl:param name="item" />
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <xsl:value-of select="$item/Author"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="svg:text[@id='item_amount_1']/svg:tspan | svg:text[(@id='item_amount_1') and (count(child::*) = 0)]">
        <xsl:param name="item" />
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <xsl:value-of select="$item/Amount/FormattedValue[1]"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="svg:text[@id='item_amount_2']/svg:tspan | svg:text[(@id='item_amount_2') and (count(child::*) = 0)]">
        <xsl:param name="item" />
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <xsl:value-of select="$item/Amount/FormattedValue[2]"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="svg:text[@id='item_amount_3']/svg:tspan | svg:text[(@id='item_amount_3') and (count(child::*) = 0)]">
        <xsl:param name="item" />
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <xsl:value-of select="$item/Amount/FormattedValue[3]"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="svg:text[@id='item_charity']/svg:tspan | svg:text[(@id='item_charity') and (count(child::*) = 0)]">
        <xsl:param name="item" />
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <xsl:value-of select="$item/Charity"/>
        </xsl:copy>
    </xsl:template>

    <!-- SVG copy with a parameter -->
    <xsl:template match="node()">
        <xsl:param name="item" />
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates>
                <xsl:with-param name="item" select="$item" />
            </xsl:apply-templates>
        </xsl:copy>
    </xsl:template>

</xsl:stylesheet>

