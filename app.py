import streamlit as st
from experta import *
import pandas as pd
import google.generativeai as genai
import os
import json

# Importar as palavras-chave 
from KeyWords import ALL_KEYWORDS_MAPPING

# Importar o motor e os fatos 
from engine import ConductEvaluationEngine, ConductDescription, ContextFact, HistoryFact, FrequencyFact, ImpactFact, NonVerbalFact, IntentionFact, HierarchicalRelationFact, ConductSeverity, Explanation, GeminiAnalysis

st.set_page_config(layout="wide", page_title="Sistema Especialista de Avaliação de Condutas UFAPE")

# --- Configuração da API do Gemini ---
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("Erro: A chave da API do Gemini (GEMINI_API_KEY) não foi encontrada nas variáveis de ambiente.")
    st.info("Por favor, defina a variável de ambiente no PowerShell/CMD com: `$env:GEMINI_API_KEY=\"SUA_CHAVE_AQUI\"` (temporário) ou adicione-a nas variáveis de ambiente do sistema (permanente).")
    st.stop()

genai.configure(api_key=API_KEY)

# --- Função de chamada do Gemini ---
def extract_keywords_with_gemini(user_description: str) -> dict:
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        keywords_prompt_parts = []
        for level_name, keywords_list in ALL_KEYWORDS_MAPPING.items():
            keywords_prompt_parts.append(f"{level_name}: {', '.join(keywords_list)}")
        keywords_string = "\n".join(keywords_prompt_parts)
        prompt = f"""
        Analise a seguinte descrição de conduta: "{user_description}"

        Com base nas palavras-chave fornecidas abaixo para cada nível de gravidade, identifique:
        1. O(s) nível(eis) de gravidade que a descrição mais fortemente sugere. Se múltiplos níveis forem sugeridos, priorize o mais alto.
        2. As palavras-chave exatas (ou sinônimos claros dos conceitos) que você encontrou na descrição que correspondem às listas abaixo.

        Palavras-chave por Nível:
        {keywords_string}

        Se a descrição não se encaixar claramente em nenhum dos níveis ou palavras-chave fornecidas, indique "Nenhum Nível Sugerido" e "Nenhuma Palavra-Chave Encontrada".

        Formato da resposta (apenas o JSON, sem texto explicativo adicional):
        ```json
        {{
            "nivel_sugerido": "Nível X" ou "Nenhum Nível Sugerido",
            "palavras_chave_encontradas": ["palavra1", "palavra2"]
        }}
        ```
        """
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith("```json") and response_text.endswith("```"):
            json_str = response_text[len("```json"): -len("```")].strip()
        else:
            json_str = response_text

        result = json.loads(json_str)
        return result
    except Exception as e:
        st.error(f"Erro ao chamar a API do Gemini ou processar a resposta: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            st.error(f"Resposta bruta do Gemini: {response.text}")
        return {"nivel_sugerido": "Nenhum Nível Sugerido", "palavras_chave_encontradas": []}

def run_expert_system(description, context, history, frequency, impact, non_verbal, intention, hierarchical_relation):
    """
    Executa o sistema especialista, declarando fatos apenas se eles forem aplicáveis.
    """
    engine = ConductEvaluationEngine()
    engine.reset()

    # Análise da descrição do usuário pelo Gemini
    st.info("Realizando análise de texto com IA (Gemini)...")
    gemini_result = extract_keywords_with_gemini(description)
    suggested_level = gemini_result.get("nivel_sugerido")
    detected_keywords = gemini_result.get("palavras_chave_encontradas", [])

    if suggested_level and suggested_level.startswith("Nível "):
        try:
            level_num = int(suggested_level.split(" ")[1])
            engine.declare(GeminiAnalysis(
                suggested_level=level_num,
                detected_keywords=detected_keywords,
                analysis_successful=True
            ))
            st.success(f"Análise do Gemini concluída. Nível base sugerido: {suggested_level}.")
        except (ValueError, IndexError):
            st.warning("Gemini sugeriu um nível inválido. A avaliação prosseguirá sem um nível base da IA.")
            engine.declare(GeminiAnalysis(analysis_successful=False))
    else:
        st.warning("O Gemini não conseguiu sugerir um nível de gravidade claro. A avaliação se baseará nos fatores adicionais.")
        engine.declare(GeminiAnalysis(analysis_successful=False))

    # --- MUDANÇA AQUI: Declarar fatos apenas se a opção não for "na" (Não se aplica) ---
    engine.declare(ConductDescription(text=description))
    if context != "na":
        engine.declare(ContextFact(context=context))
    if history != "na":
        engine.declare(HistoryFact(history=history))
    if frequency != "na":
        engine.declare(FrequencyFact(frequency=frequency))
    if impact != "na":
        engine.declare(ImpactFact(impact=impact))
    if non_verbal != "na":
        engine.declare(NonVerbalFact(non_verbal=non_verbal))
    if intention != "na":
        engine.declare(IntentionFact(intention=intention))
    if hierarchical_relation != "na":
        engine.declare(HierarchicalRelationFact(relation=hierarchical_relation))

    engine.run()

    # Lógica de coleta de resultados (sem alterações)
    final_severity = None
    ia_explanation = None
    additional_explanations = []
    
    all_severity_facts = []
    for fact_name, fact_dict in engine.log_facts:
        if fact_name == 'ConductSeverity':
            all_severity_facts.append(ConductSeverity(**fact_dict))
        elif fact_name == 'Explanation':
            exp = Explanation(**fact_dict)
            if exp['source'] == "Análise IA" or exp['source'] == "Sistema":
                ia_explanation = exp['text']
            elif exp['source'] == "Fator Adicional":
                additional_explanations.append(exp['text'])

    if all_severity_facts:
        final_severity = all_severity_facts[-1]

    return final_severity, ia_explanation, additional_explanations, engine.log_facts


# --- Interface Streamlit ---
st.title("Sistema Especialista para Avaliação de Condutas Inapropriadas - UFAPE")
st.markdown("Este sistema auxilia na avaliação da gravidade de condutas com foco em assédio e discriminação, baseado no **Guia Matriz Avaliação Gravidade Condutas** da UFAPE.")

st.header("1. Descreva a Situação")
user_description = st.text_area(
    "Por favor, descreva a conduta ou situação que você deseja avaliar:",
    height=150,
    placeholder="Ex: Em uma reunião com toda a equipe, meu chefe fez piadas sobre a minha orientação sexual."
)

st.header("2. Fatores Adicionais")
st.markdown("Selecione as opções que melhor descrevem o contexto da situação para uma avaliação mais precisa, conforme o guia da UFAPE.")

col1, col2 = st.columns(2)

# --- coluna dos fatos ---
with col1:
    context_options = {
        "na": "Não se aplica / Não informado",
        "Formal/Público": "Formal (reunião, apresentação) e Público (afetando mais pessoas)",
        "Formal/Privado": "Formal (reunião, apresentação) e Privado (apenas indivíduos específicos)",
        "Informal/Público": "Informal (evento social, conversa casual) e Público (afetando mais pessoas)",
        "Informal/Privado": "Informal (evento social, conversa casual) e Privado (apenas indivíduos específicos)",
        "Local Isolado com Conotação Sexual": "Local fechado ou isolado, com conotação sexual (aumenta vulnerabilidade)"
    }
    selected_context = st.selectbox("Contexto da conduta:", options=list(context_options.keys()), format_func=lambda x: context_options[x], index=0)

    history_options = {
        "na": "Não se aplica / Não informado",
        "Primário": "Sem histórico anterior de condutas inapropriadas",
        "Reincidente": "Histórico de condutas similares ou relacionadas",
        "Frequente": "Múltiplas reincidências que indicam um padrão comportamental"
    }
    selected_history = st.selectbox("Histórico do agressor:", options=list(history_options.keys()), format_func=lambda x: history_options[x], index=0)
    
    frequency_options = {
        "na": "Não se aplica / Não informado",
        "Isolado": "Incidente único sem repetições conhecidas",
        "Ocasional": "Ocorre esporadicamente, mas mais de uma vez",
        "Repetitivo e/ou Insistente": "Acontece frequentemente"
    }
    selected_frequency = st.selectbox("Frequência das condutas:", options=list(frequency_options.keys()), format_func=lambda x: frequency_options[x], index=0)

    impact_options = {
        "na": "Não se aplica / Não informado",
        "Não-significativo": "Não teve maiores repercussões para a vítima",
        "Negativo considerável": "Gerou consequências de curto prazo e não muito graves à vítima",
        "Negativo intenso": "Gerou consequências de médio e longo prazo, causando sofrimento"
    }
    selected_impact = st.selectbox("Impacto na vítima:", options=list(impact_options.keys()), format_func=lambda x: impact_options[x], index=0)

with col2:
    non_verbal_options = {
        "na": "Não se aplica / Não informado",
        "Neutro": "Sem sinais não-verbais significativos",
        "Agravado": "Sinais não-verbais que intensificam a negatividade (ameaça, desprezo)"
    }
    selected_non_verbal = st.selectbox("Sinais não-verbais:", options=list(non_verbal_options.keys()), format_func=lambda x: non_verbal_options[x], index=0)
    
    intention_options = {
        "na": "Não se aplica / Não informado",
        "Acidental": "Sem intenção clara de causar dano",
        "Negligente": "Falta de consideração pelas consequências",
        "Intencional": "Evidente objetivo de causar dano ou desconforto"
    }
    selected_intention = st.selectbox("Intenção percebida:", options=list(intention_options.keys()), format_func=lambda x: intention_options[x], index=0)

    hierarchical_relation_options = {
        "na": "Não se aplica / Não informado",
        "Mesmo nível hierárquico ou não relevante": "Colegas ou sem relação de subordinação direta",
        "Superior subordinado direto": "O agressor é superior direto da vítima",
        "Superior subordinado indireto": "O agressor tem posição superior, mas não direta"
    }
    selected_hierarchical_relation = st.selectbox("Relação hierárquica:", options=list(hierarchical_relation_options.keys()), format_func=lambda x: hierarchical_relation_options[x], index=0)


if st.button("Avaliar Conduta", type="primary"):
    if not user_description:
        st.warning("Por favor, descreva a situação para realizar a avaliação.")
    else:
        with st.spinner("Avaliando a conduta..."):
            final_severity, ia_explanation, additional_explanations, logged_facts = run_expert_system(
                user_description,
                selected_context,
                selected_history,
                selected_frequency,
                selected_impact,
                selected_non_verbal,
                selected_intention,
                selected_hierarchical_relation
            )

            st.success("Avaliação Concluída!")

            if final_severity:
                st.subheader("Diagnóstico do Sistema Especialista")
                
                if final_severity['level'] > 0:
                    st.markdown(f"### Nível de Gravidade Base: **{final_severity['level']} - {final_severity['description']}**")
                else:
                     st.markdown("### Nível de Gravidade Base: **Indeterminado a partir da descrição**")
                
                if ia_explanation:
                    st.info(f"**Justificativa da IA:** {ia_explanation}")

                if additional_explanations:
                    st.subheader("Análise dos Fatores Adicionais Considerados")
                    st.markdown("Os seguintes fatores contextuais foram identificados e contribuem para a análise da gravidade:")
                    for exp in additional_explanations:
                        st.markdown(f"- {exp}")
                else:
                    st.subheader("Análise dos Fatores Adicionais")
                    st.markdown("Nenhum fator adicional com potencial agravante foi selecionado para análise.")

                with st.expander("Ver Rastreabilidade da Inferência (Todos os Fatos Utilizados)"):
                    if logged_facts:
                        facts_data = [{"Tipo de Fato": f_type, "Valor": f_val} for f_type, f_val in logged_facts]
                        df_facts = pd.DataFrame(facts_data)
                        st.dataframe(df_facts, use_container_width=True)
                    else:
                        st.info("Nenhum fato foi logado.")
            else:
                st.error("Não foi possível determinar o nível de gravidade. Verifique a descrição e as configurações.")
        st.markdown("---")