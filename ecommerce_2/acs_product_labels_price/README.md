Product Labels Price - ACS
==========================

t-options='{"widget": "float", "precision": 2}'


<table width="100%" style="margin-bottom:25px"> 
                    
                    <tr style="border-bottom-style: none;">
                        <td width="80%" style="text-align: left; vertical-align: middle;  font-size: 16px;" rowspan="2">
                            <strong t-field="product.barcode"/>
                        </td>
                        <td colspan="2" style="text-align: right; font-size: 12px; border-bottom-style: none;">
                            <span t-field="product.qty_last_purchase" t-options='{"widget": "integer"}'/>
                        </td>
                    </tr>
                    
                    <tr style="border-bottom-style: none;">
                        <td></td>
                        <td style="text-align: right; font-size: 12px; border-bottom-style: none;">
                            <span t-field="product.qty_available" t-options='{"widget": "integer"}'/>
                        </td>
                    </tr>
                    
                    <tr>
                        <td style="text-align: left;">
                            1
                        </td>
                        <td style="text-align: center;">
                            2
                        </td>
                        <td style="text-align: right;">
                            3
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" style="border: 1px solid black; text-align: center;font-size: 16px; padding-bottom: 10px; padding-top: 10px;">
                            <strong t-field="product.name"/>
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align: center; font-size: 20px;" colspan="3">
                            S/ <strong t-field="product.list_price"/>
                        </td>
                    </tr>
                    <tr>
                        <strong>
                            <td style="text-align: left; font-size: 10px;">
                                <strong>PRECIO X MAYOR</strong>
                            </td>
                            <td t-if="product.wholesale_price" colspan="2" style="text-align: right; font-size: 10px;">
                                S/ <strong t-field="product.wholesale_price.fixed_price"/>
                            </td>
                            <td t-if="not product.wholesale_price" colspan="2" style="text-align: right; font-size: 10px;">
                                S/ <strong t-field="product.list_price"/>
                            </td>
                        </strong>
                    </tr>
                    
                </table>





<table width="95%" style="border-spacing:2px;margin-bottom:25px"> 
                    
                    <tr style="border-bottom-style: none;">
                        <td width="80%" style="text-align: left; vertical-align: middle;  font-size: 16px;" rowspan="2">
                            <strong t-field="product.barcode"/>
                        </td>
                        <td colspan="2" style="text-align: right; font-size: 12px; border-bottom-style: none;">
                            <span t-field="product.qty_last_purchase" t-options='{"widget": "integer"}'/>
                        </td>
                    </tr>
                    
                    <tr style="border-bottom-style: none;">
                        <td></td>
                        <td style="text-align: right; font-size: 12px; border-bottom-style: none;">
                            <span t-field="product.qty_available" t-options='{"widget": "integer"}'/>
                        </td>
                    </tr>
                    
                    <tr>
                        <td>
                            <span t-field="product.default_code"/>
                            
                        </td>
                        
                        <td style="text-align: left;">
                            <span t-if="product.date_last_purchase" t-field="product.date_last_purchase"  t-field-options='{"format": "MM"}'/>
                        </td>
                        
                        <td style="text-align: right;">
                            
                            <span style="display:inline;" t-field="product.price_last_purchase"/>
                            
                            <span style="display:inline;" t-if="product.date_last_purchase" t-field="product.date_last_purchase"  t-field-options='{"format": "YY"}'/>
 
                        </td>
                    </tr>
                    <tr>
                        <td colspan="3" style="border: 1px solid black; text-align: center;font-size: 16px; padding-bottom: 10px; padding-top: 10px;">
                            <strong t-field="product.name"/>
                        </td>
                    </tr>
                    <tr>
                        <td style="text-align: center; font-size: 20px;" colspan="3">
                            S/ <strong t-field="product.list_price"/>
                        </td>
                    </tr>
                    <tr>
                        <strong>
                            <td style="text-align: left;">
                                <strong>PRECIO X MAYOR</strong>
                            </td>
                            <td t-if="product.wholesale_price" colspan="2" style="text-align: right;">
                                S/ <strong t-field="product.wholesale_price.fixed_price"/>
                            </td>
                            <td t-if="not product.wholesale_price" colspan="2" style="text-align: right;">
                                S/ <strong t-field="product.list_price"/>
                            </td>
                        </strong>
                    </tr>
                    
                </table>





















                
