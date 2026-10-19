/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { useBus } from "@web/core/utils/hooks";
let current_user = 'User';



class ChatbotTemplate extends Component {
  static template = "odoo-mercadolibre.chatbot";

  setup() {


   //const ajax = require('web.ajax');
    this.rpc = useService("rpc");
    console.log('Component setup executed');
    this.state = useState({
      selectedMenuOption: "pending",
      isLeftSidebarVisible: true,
      isRightSidebarVisible: false,
      isCentralSidebarVisible: false,
      isEditSidebarVisible: false,
      isChatGPTConfigActive: false,
      isChecked: false,
      expandedItems: {},
      items: [
          {
              ruleActive: true,
              userInput: '¿Cuánto cuesta el envío?',
              autoResponse: 'Fast answer',
              ruleType: 'Al inicio',
          },
          {
              ruleActive: false,
              userInput: '¿Cómo hacer un seguimiento?',
              autoResponse: 'Standard answer',
              ruleType: 'Al final',
          },
          {
              ruleActive: true,
              userInput: '¿Qué opciones de pago ofrecen?',
              autoResponse: 'We offer credit/debit cards, PayPal, and bank transfer.',
              ruleType: 'Durante la compra',
          },
          {
              ruleActive: true,
              userInput: '¿Puedo cancelar mi pedido?',
              autoResponse: 'Yes, you can cancel your order within 24 hours of placing it.',
              ruleType: 'Al inicio',
          },
          {
              ruleActive: false,
              userInput: '¿Cuándo recibiré mi reembolso?',
              autoResponse: 'Reimbursement is processed within 5-7 business days.',
              ruleType: 'Después del reembolso',
          },
          {
              ruleActive: true,
              userInput: '¿Este producto está en stock?',
              autoResponse: 'You can check stock availability on the product page.',
              ruleType: 'Durante la compra',
          },
          {
              ruleActive: true,
              userInput: '¿Ofrecen descuentos por volumen?',
              autoResponse: 'Yes, we offer bulk discounts. Please contact customer service for more details.',     
              ruleType: 'Al final',
          }
      ],
    
      data: [],
      

    });
    console.log('Calling loadData...');
    this.loadData();
    this.getSessionInfo();
    this.loadRules();
  

  }


  onMessage({ detail: notifications }) {
    console.log("ACTUALIZACION")
         }
 
  selectMenuOption(option) {
    this.loadRules();

    this.state.selectedMenuOption = option;
    if (option === 'history') {
        // Si es 'history', ejecutar la función que quieres correr de nuevo
        this.loadhistory();
    }
    if (option === 'pending') {
      // Si es 'history', ejecutar la función que quieres correr de nuevo
      this.loadData();
  }

  }
  toggleQuestions(productId) {
    this.state.expandedItems[productId] = !this.state.expandedItems[productId];
  }  
  quickresponse(option) {
      console.log('Respuesta rápida seleccionada:', option);
      const textarea = document.querySelector("textarea[id^='response-']");
      if (!textarea) return;

      if (option === 'stock') {
          textarea.value = 'Hola! Sí, tenemos stock disponible para entrega inmediata.';
          textarea.focus();
      }
      if (option === 'ship') {
          textarea.value = 'Hacemos envíos a todo el país. El tiempo depende de tu ubicación.';
          textarea.focus();
      }
      if (option === 'payment') {
          textarea.value = 'Aceptamos pagos con tarjetas, Mercado Pago y otros medios habilitados.';
          textarea.focus();
      }
      if (option === 'hours') {
          textarea.value = 'Nuestro horario de atención es de lunes a sábado de 9 a.m. a 6 p.m.';
          textarea.focus();
      }
      if (option === 'promo') {
          textarea.value = 'Sí, tenemos promociones activas. ¡Consúltanos para más detalles!';
          textarea.focus();
      }
      if (option === 'warranty') {
          textarea.value = 'Todos nuestros productos son originales y tienen garantía. Te ayudamos en cualquier caso.';
          textarea.focus();
      }
      if (option === 'thanks') {
          textarea.value = '¡Gracias por tu interés! Cualquier duda adicional, estamos para ayudarte.';
          textarea.focus();
      }
      if (option === 'hi') {
          textarea.value = 'Hola. ¿Cómo podemos ayudarte?';
          textarea.focus();
      }
  }


  async getSessionInfo() {
    try {
        const session_info = await this.rpc('/web/session/get_session_info', {});

        if (session_info) {
            current_user = session_info.name;
            console.log('Usuario actual:', current_user);
        }
    } catch (error) {
        console.error('Error al obtener la información de la sesión:', error);
    }
}


async loadData() {
  try {
    // Obtener productos con meli_product_id válido
    let products = await this.rpc('/web/dataset/call_kw', {
      model: 'product.template',
      method: 'search_read',
      args: [[], ['meli_product_id', 'meli_title', 'meli_thumbnail', 'meli_actual_price']],
      kwargs: {},
    });
    console.log('🧩 Productos MELI', products);

    // Filtrar productos con meli_product_id definido
    let productIds = products.map(p => p.meli_product_id).filter(Boolean);

    // Obtener preguntas UNANSWERED (evita BANNED)
    let questions = await this.rpc('/web/dataset/call_kw', {
      model: 'vex.meli.questions',
      method: 'search_read',
      args: [
        [
          ['meli_item_id', 'in', productIds],
          ['meli_status', '=', 'UNANSWERED'],
          ['meli_answer', '=', false]
        ],
        [
          'meli_item_id', 'meli_text', 'meli_answer', 'meli_created_at',
          'meli_from_id', 'meli_id', 'meli_from_nickname',
          'meli_answered_at', 'meli_answered_from_odoo', 'meli_odoo_answerer'
        ]
      ],
      kwargs: {},
    });

    console.log('📩 Preguntas UNANSWERED', questions);

    // Ordenar preguntas por fecha (más reciente primero)
    questions.sort((a, b) => new Date(b.meli_created_at) - new Date(a.meli_created_at));

    // Asociar preguntas a productos
    let productsWithQuestions = products
      .filter(product => questions.some(q => q.meli_item_id === product.meli_product_id))
      .map(product => {
        const qList = questions.filter(q => q.meli_item_id === product.meli_product_id);
        return {
          ...product,
          meli_title: `${product.meli_title} (${qList.length} pregunta${qList.length > 1 ? 's' : ''} sin responder)`,
          questions: qList,
          latest_question_date: new Date(qList[0].meli_created_at),
        };
      });

    // Ordenar productos por la fecha de la última pregunta
    productsWithQuestions.sort((a, b) => b.latest_question_date - a.latest_question_date);
    productsWithQuestions.forEach(p => delete p.latest_question_date);

    // Cargar en el estado
    this.state.data = productsWithQuestions;
    console.log('✅ Estado final cargado:', this.state.data);

  } catch (error) {
    console.error('❌ Error al cargar datos:', error);
  }
}



  async loadhistory(cargar_historia) {
    try {
      // Obtener productos con meli_id válido
      let products = await this.rpc('/web/dataset/call_kw', {
        model: 'product.template',
        method: 'search_read',
        args: [[], ['meli_product_id', 'meli_title', 'meli_thumbnail', 'meli_actual_price']],
        kwargs: {},
      });
      console.log('Productos MELI', products);

      // Obtener preguntas filtradas
      let productIds = products.map(p => p.meli_product_id);
      let questions = await this.rpc('/web/dataset/call_kw', {
        model: 'vex.meli.questions',
        method: 'search_read',
        args: [[['meli_item_id', 'in', productIds], ['meli_answer', '!=', false]], ['meli_item_id', 'meli_text', 'meli_answer', 'meli_created_at', 'meli_from_id', 'meli_id', 'meli_from_nickname', 'meli_answered_at', 'meli_answered_from_odoo', 'meli_odoo_answerer']],
        kwargs: {},
      });

      console.log('Questions MELI', questions);

      // Procesar preguntas
      questions = questions.map(question => {
        if (question.meli_created_at && question.meli_answered_at) {
          let createdDate = new Date(question.meli_created_at);
          let answeredDate = new Date(question.meli_answered_at);
          let differenceMs = answeredDate - createdDate;
          let days = Math.floor(differenceMs / (1000 * 60 * 60 * 24));
          let hours = Math.floor((differenceMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
          let minutes = Math.floor((differenceMs % (1000 * 60 * 60)) / (1000 * 60)).toString().padStart(2, '0');
          question.meli_answered_at = (days > 0 ? `${days}d ` : '') + `${hours}hr ${minutes}min`;
        }

        question.meli_answered_from_odoo = question.meli_odoo_answerer
          ? `Odoo : ${question.meli_odoo_answerer}`
          : "Mercado Libre";

        return question;
      });

      // Ordenar preguntas por fecha de creación descendente (más reciente primero)
      questions.sort((a, b) => new Date(b.meli_created_at) - new Date(a.meli_created_at));

      // Mapear preguntas a productos
      let productsWithQuestions = products.map(product => {
        const qList = questions.filter(q => q.meli_item_id === product.meli_product_id);
        return {
          ...product,
          questions: qList,
          latest_question_date: qList.length ? new Date(qList[0].meli_created_at) : null,
        };
      }).filter(product => product.questions.length > 0);

      // Ordenar productos según la fecha más reciente de pregunta
      productsWithQuestions.sort((a, b) => b.latest_question_date - a.latest_question_date);

      // Eliminar campo auxiliar antes de mostrar
      productsWithQuestions.forEach(p => delete p.latest_question_date);

      // Actualizar el estado
      this.state.data = productsWithQuestions;

      console.log('Data loaded:', this.state.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  }

  toggleSidebar(side) {
    this.loadRules();
    
    switch (side) {
      case "left":
        this.state.isLeftSidebarVisible = !this.state.isLeftSidebarVisible;
        break;
      case "right":
        this.state.isRightSidebarVisible = !this.state.isRightSidebarVisible;
        this.loadGptConfig()
        break;
      case "central":
        this.state.isCentralSidebarVisible = !this.state.isCentralSidebarVisible;
        break;
      case "edit":
        this.state.isEditSidebarVisible = !this.state.isEditSidebarVisible;
        break;
    
      default:
        break;
    }
  }




  toggleRuleSidebar() {
    this.state.isRuleSidebarVisible = !this.state.isRuleSidebarVisible;
    
}



  toggleIsChatGPTConfigActive() {
    this.state.isChatGPTConfigActive = !this.state.isChatGPTConfigActive;
    this.UpdateGptBool(this.state.isChatGPTConfigActive);

  }

  async UpdateGptBool(bool_value) {
    try {
        // Realizar la llamada al servidor
        let updateRule = await this.rpc('/web/dataset/call_kw', {
            model: 'vex.gpt.config',
            method: 'update_gpt_config',
            args: [],
            kwargs: {
                enable_gpt_responder: bool_value,             
            }
        });
        console.log("Estado sincronizado correctamente:", bool_value);
    } catch (error) {
        console.error("Error al sincronizar el estado:", error);
    }
}

 async botonResponder(itemId, element_id) {
    const responseText = document.getElementById('response-' + itemId).value;

    if (!responseText.trim()) {
        alert('No puedes enviar una respuesta vacía.');
        return;
    }

    console.log('Question ID:', itemId);
    console.log('Respuesta a enviar:', responseText);
    console.log('Item ID:', element_id);

    try {
        // Obtener el access token de Mercado Libre
        let instanceResult = await this.rpc('/web/dataset/call_kw', {
            model: 'vex.instance',
            method: 'search_read',
            args: [],
            kwargs: {
                fields: ['meli_access_token'], // Especifica el campo que deseas leer
            },
        });
        
        // Logging para verificar los datos retornados
        console.log('Datos retornados por search_read:', instanceResult);

       
        
        //let accessToken = instanceResult[0].meli_access_token;
        let accessToken = 0; // Anotaciones Luis: Le posieron 0 xq en el python capturan el access token
        console.log(accessToken);

        // Enviar la respuesta a la pregunta llamando a la funcion de python
        let answerResult = await this.rpc('/web/dataset/call_kw', {
            model: 'vex.import.wizard',
            method: 'answer_question',
            args: [itemId, responseText, accessToken],
            kwargs: {},
        });
        console.log('answerResult',answerResult)
        if (answerResult) {
            console.log('Respuesta enviada correctamente.');

            // Actualizar el campo `meli_answer` en `vex.meli.questions` con la respuesta
            let questions = await this.rpc('/web/dataset/call_kw', {
                model: 'vex.meli.questions',
                method: 'search_read',
                args: [[['meli_id', '=', itemId]], ['id', 'meli_answer']], // Obtener el id para poder hacer el write
                kwargs: {},
            });

            if (questions.length > 0) {
                let questionId = questions[0].id; // Obtener el ID de la pregunta
                let currentDate = new Date();

                let formattedDate = currentDate.getFullYear() + '-' + 
                String(currentDate.getMonth() + 1).padStart(2, '0') + '-' + 
                String(currentDate.getDate()).padStart(2, '0') + ' ' + 
                String(currentDate.getHours()).padStart(2, '0') + ':' + 
                String(currentDate.getMinutes()).padStart(2, '0') + ':' + 
                String(currentDate.getSeconds()).padStart(2, '0');

                console.log(formattedDate);

                // Actualizar el valor de `meli_answer` en la base de datos
                await this.rpc('/web/dataset/call_kw', {
                    model: 'vex.meli.questions',
                    method: 'write',
                    args: [[questionId], { 'meli_answer': responseText, 'meli_odoo_answerer': current_user, 'meli_answered_at': formattedDate , 'meli_status' : "ANSWERED"}],
                    kwargs: {},
                });

                console.log('El campo meli_answer ha sido actualizado correctamente.');
                this.loadData(); // Recargar los datos
                // Aquí puedes agregar cualquier lógica adicional para imprimir la respuesta si es necesario

            } else {
                console.error('No se encontró ninguna pregunta.');
            }
        } else {
            alert('Error al enviar la respuesta.');
        }
    } catch (error) {
        console.error('Error al procesar la solicitud:', error);
        alert('Hubo un error al procesar la solicitud.');
    }
}

async deleteButtonClick(questionid) {
  const confirmation = confirm('¿Estás seguro de borrar esto?');

  if (confirmation) {
      // Si el usuario hace clic en "Aceptar"
      console.log(`Borrar elemento con id: ${questionid}`);

      try {
          // Obtener el access token de Mercado Libre
          let instanceResult = await this.rpc('/web/dataset/call_kw', {
              model: 'vex.instance',
              method: 'search_read',
              args: [],
              kwargs: {
                  fields: ['meli_access_token'],
              },
          });

          let accessToken = instanceResult[0].meli_access_token;
          console.log(accessToken);

          // Llamar al método para eliminar la pregunta en Mercado Libre
          let deleteResult = await this.rpc('/web/dataset/call_kw', {
              model: 'vex.import.wizard',
              method: 'delete_question',
              args: [questionid, accessToken],
              kwargs: {},
          });

          if (deleteResult) {
              console.log('Respuesta eliminada correctamente de Mercado Libre');

              // Si la respuesta fue eliminada, buscar el ID de la pregunta en Odoo
              let questions = await this.rpc('/web/dataset/call_kw', {
                  model: 'vex.meli.questions',
                  method: 'search_read',
                  args: [[['meli_id', '=', questionid]], ['id', 'meli_answer']], // Obtener el id para hacer el delete
                  kwargs: {},
              });

              if (questions.length > 0) {
                  let questionId = questions[0].id; // Obtener el ID de la pregunta

                  // Eliminar la pregunta de la base de datos
                  await this.rpc('/web/dataset/call_kw', {
                      model: 'vex.meli.questions',
                      method: 'unlink',
                      args: [[questionId]],
                      kwargs: {},
                  });

                  console.log('La pregunta ha sido eliminada correctamente de la base de datos.');
                  this.loadData(); // Recargar los datos
              } else {
                  console.error('No se encontró ninguna pregunta.');
              }
          } else {
              alert('Error al eliminar la respuesta en Mercado Libre.');
          }
      } catch (error) {
          console.error('Error al procesar la solicitud:', error);
          alert('Hubo un error al procesar la solicitud.');
      }
  } else {
      // Si el usuario hace clic en "Cancelar"
      console.log('El usuario canceló la operación');
  }
}

// Automatic response  logic


async loadRules() {
  // Llamada JSON-RPC con los parámetros en kwargs
  let rules = await this.rpc('/web/dataset/call_kw', {
      model: 'vex.auto.response',
      method: 'get_auto_responses',
      args: [],  
      kwargs: {}
  });
  this.state.items = rules;
  console.log("Rules",rules);
  
}

async loadGptConfig() {
  // Llamada JSON-RPC con los parámetros en kwargs
  let gpt_config = await this.rpc('/web/dataset/call_kw', {
      model: 'vex.gpt.config',
      method: 'get_gpt_config',
      args: [],  
      kwargs: {}
  });
 

  this.state.isChatGPTConfigActive = gpt_config.enable_gpt_responder;
  //const gpt_key = document.querySelector("#openAIAPIKeyInp");
  const responseText = document.getElementById("openApiKey");
  responseText.value = gpt_config.chatgpt_key;
  const usage = document.getElementById("usageLimit");
  usage.value = gpt_config.daily_usage_limit;
  
  
  
}

async createNewRule(answerText, autoResponse, ruleType) {
  // Llamada JSON-RPC con los parámetros en kwargs
  let number = await this.rpc('/web/dataset/call_kw', {
      model: 'vex.auto.response',
      method: 'create_auto_response_entry',
      args: [],  // Deja args vacío si estás usando kwargs
      kwargs: {
          user_input: answerText,     // Parametro esperado en Python
          auto_answer: autoResponse,       // Parametro esperado en Python
          rule_type: ruleType ,  // Valor predeterminado si no se especifica
          is_rule_active: false           // Puedes personalizar este valor
      }
  });
  console.log("respuesta", number);
  this.toggleSidebar('central');
  this.loadRules();
}

createRule() {
  // Captura los valores de los inputs
  const answerText = document.querySelector("#answerText").value;
  const autoResponse = document.querySelector("#autoResponse").value;
  
  const ruleType = document.querySelector("#ruleType").value;

  // Verifica que todos los campos estén llenos
  if (!answerText || !autoResponse || !ruleType) {
      alert("Todos los campos son obligatorios.");
      return; // Detiene la ejecución si falta algún campo
  }

  // Si todos los campos tienen valor, imprime los valores en la consola
  console.log({
      answerText,
      autoResponse,

      ruleType,
  });
  this.createNewRule(answerText,autoResponse,ruleType);
}

onCheckboxChange(event) {
  // Obtener el id del checkbox y su estado
  const checkboxId = event.target.id;  // El id del checkbox
  const isChecked = event.target.checked;  // Estado del checkbox (true o false)

  console.log('Checkbox ID:', checkboxId);  // Muestra el id del checkbox
  console.log('Checkbox Estado:', isChecked);  // Muestra el estado del checkbox

  // Aquí puedes realizar cualquier acción que necesites con el id y el estado
  // Ejemplo: actualizar el estado en tu modelo o enviar información al servidor
  this.updateRuleIsActive(checkboxId,isChecked);
}

async updateRuleIsActive(id,newStatus){
  let updateRule = await this.rpc('/web/dataset/call_kw', {
    model: 'vex.auto.response',
    method: 'set_rule_active_status',
    args: [],  
    kwargs: {
      rule_id: id,     
      is_active: newStatus
    }
  });

  console.log(updateRule);

}

async deleteRule(ev) {
  const itemId = ev.target.id; 
  
  // Aquí puedes agregar la lógica para eliminar la regla
  let updateRule = await this.rpc('/web/dataset/call_kw', {
    model: 'vex.auto.response',
    method: 'deleteRule',
    args: [],  
    kwargs: {
      record_id: itemId
    }
  });

  console.log('Eliminar regla con id:', itemId,updateRule);
  this.loadRules();

}

 async editeRule(ev) {
  const itemId = ev.target.id; 
  
  // Aquí puedes agregar la lógica para eliminar la regla
  let rule_data = await this.rpc('/web/dataset/call_kw', {
    model: 'vex.auto.response',
    method: 'get_rule_by_id',
    args: [],  
    kwargs: {
      response_id: itemId
    }
  });

  console.log('Datos', itemId,rule_data);
  this.toggleSidebar('edit');

  const NewanswerText = document.querySelector("#answerText_edit");
  const NewautoResponse = document.querySelector("#autoResponse_edit");
  const NewruleType = document.querySelector("#ruleType_edit");
  const edit_button = document.querySelector("#button_edit");

  NewanswerText.value = rule_data.userInput;
  NewautoResponse.value = rule_data.autoResponse;
  NewruleType.value = rule_data.ruleType;

  //edit_button.id = itemId;
  edit_button.setAttribute("rule-to-edit-id", itemId);


}

async udpateRuleData(event){
  const NewanswerText = document.querySelector("#answerText_edit").value;
  const NewautoResponse = document.querySelector("#autoResponse_edit").value;
  const NewruleType = document.querySelector("#ruleType_edit").value;
  
  const Id = event.target.id; 
  const edit_button = document.querySelector(`#${Id}`);
  
  const id_rule = edit_button.getAttribute("rule-to-edit-id");
  

  //console.log(NewanswerText,NewautoResponse,NewruleType, Id);
  

  let rule_data = await this.rpc('/web/dataset/call_kw', {
    model: 'vex.auto.response',
    method: 'update_rule',
    args: [],  
    kwargs: {
      response_id: id_rule,
      isRuleActive: false,
      userInput: NewanswerText,
      autoAnswer: NewautoResponse,
      ruleType: NewruleType

    }
  });

  console.log(rule_data);

  this.loadRules();
  this.toggleSidebar('edit')



  
}


async updateGptData(){


  
  //const gpt_key = document.querySelector("#openAIAPIKeyInp");
  const api_key = document.getElementById("openApiKey").value;  
  const usage_value = document.getElementById("usageLimit").value;
  const is_gpt_active = this.state.isChatGPTConfigActive
      

  

  let gpt_update = await this.rpc('/web/dataset/call_kw', {
    model: 'vex.gpt.config',
    method: 'update_gpt_config',
    args: [],  
    kwargs: {
      enable_gpt_responder: is_gpt_active,
      chatgpt_key: api_key,
      daily_usage_limit: usage_value
    }
  });

  console.log(gpt_update);
  this.toggleSidebar('right');

  
  

}


}

registry.category("actions").add("odoo-mercadolibre.chatbot", ChatbotTemplate);
