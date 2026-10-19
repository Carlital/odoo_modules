$(document).ready(function () {

    const recargoProviderId = 17;
    let recargoAplicado = false;

    const intervalId = setInterval(function () {
        const paymentMethodSection = $('#payment_method');
        const paymentMethodInputs = paymentMethodSection.find('input[name="o_payment_radio"]');

        if (paymentMethodInputs.length === 0) {
            return;
        }

        clearInterval(intervalId);

        paymentMethodInputs.on('change', function () {

            const selectedProviderId = parseInt($(this).data('provider-id'), 10);

            // Eliminar el recargo
            if (selectedProviderId !== recargoProviderId) {
                $('#extra_fee_info').hide();
                $('#extra_fee_row').remove();
                
                // Restablecer el total
                let subtotalText = $('#order_total_untaxed .oe_currency_value').text().trim();
                subtotalText = subtotalText.replace(/[^\d.-]/g, '').replace(',', '.');
                const subtotal = parseFloat(subtotalText);

                let taxText = $('#order_total_taxes .oe_currency_value').text().trim();
                taxText = taxText.replace(/[^\d.-]/g, '').replace(',', '.');
                const taxAmount = parseFloat(taxText) || 0;

                const newTotal = subtotal + taxAmount;
                $('#order_total .oe_currency_value').text(newTotal.toFixed(2));

                recargoAplicado = false;
                return;
            }

            if (recargoAplicado) {
                return;
            }

            // Solicitud AJAX
            $.ajax({
                url: '/acs_izipay_extra_fees/get_surcharge_info',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ provider_id: selectedProviderId }),
                success: function (response) {

                    const resultData = response.result?.result || {};
                    const surchargePercentage = resultData.surcharge_percentage || 0;
                    const surchargeProductId = resultData.surcharge_product_id;
                    const surchargeProductName = resultData.surcharge_product_name || "Recargo";

                    if (surchargePercentage > 0 && surchargeProductId) {

                        // Obtener subtotal
                        let subtotalText = $('#order_total_untaxed .oe_currency_value').text().trim();
                        subtotalText = subtotalText.replace(/[^\d.-]/g, '').replace(',', '.');
                        const subtotal = parseFloat(subtotalText);

                        // Obtener impuestos
                        let taxText = $('#order_total_taxes .oe_currency_value').text().trim();
                        taxText = taxText.replace(/[^\d.-]/g, '').replace(',', '.');
                        const taxAmount = parseFloat(taxText) || 0;

                        if (isNaN(subtotal) || isNaN(taxAmount)) {
                            console.error("Error al convertir el subtotal o impuestos a número.");
                            $('#extra_fee_info').hide();
                            return;
                        }

                        // Calcular recargo (subtotal e impuestos)
                        const totalBase = subtotal + taxAmount;
                        const surchargeAmount = totalBase * (surchargePercentage / 100);

                        $('#extra_fee_info').show();
                        $('#extra_fee_amount').text(surchargeAmount.toFixed(2));

                        const newTotal = totalBase + surchargeAmount;
                        $('#order_total .oe_currency_value').text(newTotal.toFixed(2));

                        // Eliminar recargo en la interfaz
                        $('#extra_fee_row').remove();
                        $('#order_total_taxes').after(
                            `<tr id="extra_fee_row" class="order_line_surcharge">
                                <td colspan="2" class="text-start text-muted border-0 ps-3">${surchargeProductName} (${surchargePercentage}%)</td>
                                <td class="text-end text-muted border-0 pe-3">S/ <span id="extra_fee_display" class="oe_currency_value">${surchargeAmount.toFixed(2)}</span></td>
                             </tr>`
                        );

                        recargoAplicado = true;  
                    } else {
                        $('#extra_fee_info').hide();
                        $('#extra_fee_row').remove();
                        recargoAplicado = false;
                    }
                },
                error: function (error) {
                    console.error("Error en la solicitud AJAX para obtener el recargo:", error);
                    $('#extra_fee_info').hide();
                    $('#extra_fee_row').remove();
                    recargoAplicado = false;
                }
            });
        });

        paymentMethodInputs.filter(':checked').trigger('change');
    }, 500);
});
