/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";


export class BcPlanGalleryField extends Component {
    static template = "bc.BcPlanGalleryField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            loading: false,
            plans: [],
        });

        onWillStart(async () => {
            await this._loadPlans();
        });

        onWillUpdateProps(async (nextProps) => {
            const prevSub = this.props.value;
            const nextSub = nextProps.value;
            if (prevSub !== nextSub) {
                await this._loadPlans(nextProps);
            }
        });
    }

    _getSubcampaignId(props) {
        return props?.value || false;
    }

    async _loadPlans(forcedProps) {
        const subId = this._getSubcampaignId(forcedProps || this.props);

        if (!subId) {
            this.state.plans = [];
            return;
        }

        this.state.loading = true;
        try {
            const plans = await this.orm.searchRead(
                "bc.plan",
                [
                    ["subcampaign_id", "=", subId],
                    ["active", "=", true],
                ],
                [
                    "name",
                    "headline",
                    "price_with_tax",
                    "currency_id",
                    "line_ids",
                    "id",
                    "sequence",
                    "active",
                ],
                { order: "sequence, id" }
            );

            const allLineIds = plans.flatMap((p) => p.line_ids);
            const linesByPlan = {};
            if (allLineIds.length) {
                const lines = await this.orm.searchRead(
                    "bc.plan.line",
                    [
                        ["id", "in", allLineIds],
                        ["active", "=", true],
                    ],
                    [
                        "plan_id",
                        "sequence",
                        "titulo",
                        "detalle",
                        "icon_hint",
                        "tipo",
                        "icon_ids",
                        "id",
                    ],
                    { order: "plan_id, sequence, id" }
                );
                for (const ln of lines) {
                    const pid = Array.isArray(ln.plan_id) ? ln.plan_id[0] : ln.plan_id;
                    if (!linesByPlan[pid]) {
                        linesByPlan[pid] = [];
                    }
                    linesByPlan[pid].push(ln);
                }
            }

            for (const p of plans) {
                p.lines = linesByPlan[p.id] || [];
                let currencyDisplay = '';
                if (p.currency_id) {
                    if (Array.isArray(p.currency_id)) {
                        currencyDisplay = p.currency_id[1] || '';
                        p.currency_id = p.currency_id[0];
                    } else {
                        currencyDisplay = '';
                    }
                }
                p.currency_name = currencyDisplay;
            }

            // Recopilar todos los iconos y leer binarios/mimetype
            const iconIds = [];
            for (const p of plans) {
                for (const ln of p.lines) {
                    if (ln.icon_ids && ln.icon_ids.length) {
                        iconIds.push(...ln.icon_ids);
                    }
                }
            }
            let iconMap = {};
            if (iconIds.length) {
                const icons = await this.orm.searchRead(
                    "bc.icon",
                    [["id", "in", iconIds]],
                    ["name", "mimetype", "image_128", "image"]
                );
                iconMap = Object.fromEntries(icons.map(i => [i.id, i]));
            }
            // Inyectar array listo para <img>
            for (const p of plans) {
                for (const ln of p.lines) {
                    ln.icons = (ln.icon_ids || []).map(id => {
                        const ic = iconMap[id];
                        if (!ic) return null;
                        const data = ic.image_128 || ic.image;
                        const mimetype = ic.mimetype || "image/png";
                        if (!data) return null;
                        return {
                            name: ic.name,
                            src: `data:${mimetype};base64,${typeof data === 'string' ? data : ''}`,
                        };
                    }).filter(Boolean);
                }
            }

            this.state.plans = plans;
        } catch (err) {
            console.error("[crm_custom_campaign_ext_UI] Error cargando planes:", err);
            this.notification.add("No se pudieron cargar los planes.", {
                type: "danger",
            });
        } finally {
            this.state.loading = false;
        }
    }

    async selectPlan(planId) {
        if (!planId) {
            return;
        }
        await this.props.record.update({ bc_plan_id: planId });
        this.notification.add("Plan seleccionado.", { type: "success" });
    }
}

registry
.category("fields")
.add("bc_plan_gallery", {
    component: BcPlanGalleryField,
    supportedTypes: ["many2one"],
});
