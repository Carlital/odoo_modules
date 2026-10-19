/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, useRef, onMounted } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

/**
 * Galería comercial de una subcampaña
 * - Se monta en <field name="campaign_id" widget="bc_subcampaign_gallery"/>
 * - Muestra todos los bc.plan activos de la subcampaña actual
 * - Cada plan muestra sus bc.plan.line activos (bloques comerciales)
 * - Drag & Drop para reordenar planes
 * - Acciones rápidas en hover
 */
export class BcSubcampaignGalleryField extends Component {
    static template = "bc.BcSubcampaignGalleryField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");

        this.state = useState({
            loading: false,
            plans: [],
            draggedPlanId: null,
        });

        this.galleryRef = useRef("galleryContainer");

        onWillStart(async () => {
            await this._loadPlansForCurrentSubcampaign();
        });

        onMounted(() => {
            this._setupDragAndDrop();
        });
    }

    /**
     * Queremos el ID REAL de la subcampaña abierta (el registro bc.subcampaign en el form).
     * Podemos leerlo desde las props del componente.
     */
    _getCurrentSubcampaignId() {
        // En un componente OWL (Odoo 18), los datos del campo están en `this.props.record`
        const recordId = this.props.record.resId;

        // Si el registro aún no ha sido guardado, `resId` será `false`
        if (!recordId) {
            console.warn(
                "[crm_custom_campaign_ext_UI] No pude determinar subcampaign_id en BcSubcampaignGalleryField"
            );
        }
        return recordId;
    }

    async _loadPlansForCurrentSubcampaign() {
        const subId = this._getCurrentSubcampaignId();
        if (!subId) {
            this.state.plans = [];
            return;
        }

        this.state.loading = true;
        try {
            // 1. Traer planes activos de esa subcampaña
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

            // 2. Traer líneas activas (bloques comerciales) con iconos
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
                        "tipo",
                        "icon_hint",
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

            // 3. Cargar iconos asociados a las líneas
            const allIconIds = Object.values(linesByPlan)
                .flat()
                .flatMap(ln => ln.icon_ids || []);
            
            let iconMap = {};
            if (allIconIds.length) {
                const icons = await this.orm.searchRead(
                    "bc.icon",
                    [["id", "in", [...new Set(allIconIds)]]],
                    ["name", "mimetype", "image_128", "image"]
                );
                iconMap = Object.fromEntries(icons.map(i => [i.id, i]));
            }

            // 4. Adjuntar líneas e iconos en cada plan
            for (const p of plans) {
                p.lines = linesByPlan[p.id] || [];
                
                // Inyectar iconos en cada línea
                for (const ln of p.lines) {
                    ln.icons = (ln.icon_ids || []).map(id => {
                        const ic = iconMap[id];
                        if (!ic) return null;
                        const data = ic.image_128 || ic.image;
                        const mimetype = ic.mimetype || "image/png";
                        if (!data) return null;
                        return {
                            name: ic.name || 'Icon',
                            src: `data:${mimetype};base64,${typeof data === 'string' ? data : ''}`,
                        };
                    }).filter(Boolean);
                }
                
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
                
                // Preparar la clase CSS basada en el nombre del plan
                p.planClass = (p.name || '').toLowerCase().replace(/\s+/g, '');
            }

            this.state.plans = plans;

            console.log(
                "[crm_custom_campaign_ext_UI] Gallery subcampaign plans:",
                plans
            );
        } catch (err) {
            console.error(
                "[crm_custom_campaign_ext_UI] Error cargando planes subcampaña:",
                err
            );
        } finally {
            this.state.loading = false;
        }
    }

    // ========== DRAG & DROP ==========
    _setupDragAndDrop() {
        // Los event listeners se manejan desde el template con t-on-*
    }

    onDragStart(planId, ev) {
        this.state.draggedPlanId = planId;
        ev.dataTransfer.effectAllowed = "move";
        ev.target.style.opacity = "0.5";
    }

    onDragEnd(ev) {
        ev.target.style.opacity = "1";
        this.state.draggedPlanId = null;
    }

    onDragOver(ev) {
        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";
    }

    async onDrop(targetPlanId, ev) {
        ev.preventDefault();
        
        const draggedId = this.state.draggedPlanId;
        if (!draggedId || draggedId === targetPlanId) {
            return;
        }

        // Encontrar índices
        const draggedIndex = this.state.plans.findIndex(p => p.id === draggedId);
        const targetIndex = this.state.plans.findIndex(p => p.id === targetPlanId);

        if (draggedIndex === -1 || targetIndex === -1) {
            return;
        }

        // Reordenar en el array local
        const plans = [...this.state.plans];
        const [draggedPlan] = plans.splice(draggedIndex, 1);
        plans.splice(targetIndex, 0, draggedPlan);

        // Actualizar sequences
        const updates = [];
        for (let i = 0; i < plans.length; i++) {
            plans[i].sequence = (i + 1) * 10;
            updates.push({
                id: plans[i].id,
                sequence: plans[i].sequence,
            });
        }

        this.state.plans = plans;

        // Guardar en BD
        try {
            for (const update of updates) {
                await this.orm.write("bc.plan", [update.id], {
                    sequence: update.sequence,
                });
            }
            this.notification.add("Orden de planes actualizado", { type: "success" });
        } catch (err) {
            console.error("Error actualizando orden:", err);
            this.notification.add("Error al guardar el orden", { type: "danger" });
            await this._loadPlansForCurrentSubcampaign(); // Recargar
        }
    }

    // ========== ACCIONES RÁPIDAS ==========
    async onEditPlan(planId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "bc.plan",
            res_id: planId,
            views: [[false, "form"]],
            target: "new",
            context: {},
        });
    }

    async onToggleActive(planId) {
        const plan = this.state.plans.find(p => p.id === planId);
        if (!plan) return;

        try {
            await this.orm.write("bc.plan", [planId], {
                active: !plan.active,
            });
            plan.active = !plan.active;
            this.notification.add(
                plan.active ? "Plan activado" : "Plan desactivado",
                { type: "success" }
            );
        } catch (err) {
            console.error("Error toggling active:", err);
            this.notification.add("Error al cambiar estado", { type: "danger" });
        }
    }

    async onDuplicatePlan(planId) {
        try {
            const newId = await this.orm.call("bc.plan", "copy", [planId]);
            this.notification.add("Plan duplicado", { type: "success" });
            await this._loadPlansForCurrentSubcampaign();
        } catch (err) {
            console.error("Error duplicating plan:", err);
            this.notification.add("Error al duplicar plan", { type: "danger" });
        }
    }

    async onArchivePlan(planId) {
        try {
            await this.orm.write("bc.plan", [planId], { active: false });
            this.notification.add("Plan archivado", { type: "success" });
            await this._loadPlansForCurrentSubcampaign();
        } catch (err) {
            console.error("Error archiving plan:", err);
            this.notification.add("Error al archivar plan", { type: "danger" });
        }
    }
}

// Registrar el widget como field widget
registry
    .category("fields")
        .add("bc_subcampaign_gallery", {
            component: BcSubcampaignGalleryField,
            supportedTypes: ["many2one"],
        });
