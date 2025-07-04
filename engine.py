from experta import *

# --- Definição dos Fatos ---

class ConductDescription(Fact):
    """Fato que representa a descrição textual da conduta fornecida pelo usuário."""
    text = Field(str)

class ContextFact(Fact):
    """Fato que representa o contexto em que a conduta ocorreu."""
    context = Field(str, mandatory=True)

class HistoryFact(Fact):
    """Fato que representa o histórico de condutas do agressor."""
    history = Field(str, mandatory=True)

class FrequencyFact(Fact):
    """Fato que representa a frequência da conduta."""
    frequency = Field(str, mandatory=True)

class ImpactFact(Fact):
    """Fato que representa o impacto da conduta na vítima."""
    impact = Field(str, mandatory=True)

class NonVerbalFact(Fact):
    """Fato que representa os sinais não-verbais que acompanham a conduta."""
    non_verbal = Field(str, mandatory=True)

class IntentionFact(Fact):
    """Fato que representa a intenção percebida do agressor."""
    intention = Field(str, mandatory=True)

class HierarchicalRelationFact(Fact):
    """Fato que representa a relação hierárquica entre agressor e vítima."""
    relation = Field(str, mandatory=True)

class ConductSeverity(Fact):
    """Fato que representa o nível de gravidade da conduta."""
    level = Field(int, mandatory=True)
    description = Field(str, mandatory=True)

class Explanation(Fact):
    """Fato para armazenar explicações geradas pelo motor de inferência."""
    text = Field(str, mandatory=True)
    source = Field(str, mandatory=True, default="Base") # "Base" para o nível, "Fator Adicional" para os demais

class GeminiAnalysis(Fact):
    """
    Fato que representa a análise da descrição do usuário pelo Gemini,
    incluindo o nível de gravidade sugerido e as palavras-chave encontradas.
    """
    suggested_level = Field(int, mandatory=False)
    detected_keywords = Field(list, mandatory=False)
    analysis_successful = Field(bool, mandatory=True, default=False)

# --- Motor de Inferência ---

class ConductEvaluationEngine(KnowledgeEngine):
    """
    Motor de inferência para avaliação da gravidade de condutas,
    utilizando as regras do Guia Matriz Avaliação Gravidade Condutas da UFAPE.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_facts = []

    def declare(self, fact):
        """Sobrescreve o método declare para logar os fatos."""
        super().declare(fact)
        self.log_facts.append((fact.__class__.__name__, fact.as_dict()))

    @DefFacts()
    def _initial_facts(self):
        """Fatos iniciais que podem ser úteis para o motor."""
        yield Fact(system_initialized=True)

    # --- Regras para Níveis de Gravidade (Baseadas na análise do Gemini) ---
    # Estas regras têm alta prioridade (salience) para definir o nível base inicial.

    @Rule(AS.gemini_data << GeminiAnalysis(analysis_successful=True, suggested_level=W()), ~ConductSeverity(), salience=20)
    def set_base_severity_from_gemini(self, gemini_data):
        """Define o nível de gravidade base com base na análise bem-sucedida do Gemini."""
        level = gemini_data['suggested_level']
        description = self._get_severity_description(level)
        self.declare(ConductSeverity(level=level, description=description))
        
        keywords_text = f"Palavras-chave detectadas: {', '.join(gemini_data['detected_keywords'])}." if gemini_data.get('detected_keywords') else "Nenhuma palavra-chave específica foi detectada, mas a análise contextual sugeriu este nível."
        self.declare(Explanation(
            text=f"A análise da IA (Gemini) sugere um **Nível Base {level} ({description})** para a conduta descrita. {keywords_text}",
            source="Análise IA"
        ))

    @Rule(GeminiAnalysis(analysis_successful=False), ~ConductSeverity(), salience=5)
    def fallback_no_gemini_suggestion(self):
        """Se o Gemini falhar, define um nível padrão e informa o usuário."""
        self.declare(ConductSeverity(level=0, description="Indeterminado pela IA"))
        self.declare(Explanation(
            text="A IA não conseguiu determinar um nível de gravidade claro a partir da descrição. A avaliação se baseará apenas nos fatores adicionais selecionados.",
            source="Sistema"
        ))

    # --- REGRAS NOVAS: Fatores Adicionais geram EXPLICAÇÕES, não alteram o nível ---
    # Estas regras verificam os fatos adicionais e adicionam explicações contextuais.
    # Elas não alteram o nível de gravidade, apenas enriquecem o diagnóstico final.

    @Rule(ContextFact(context="Local Isolado com Conotação Sexual"))
    def explain_context_sexual(self):
        # Conforme o guia, locais isolados com conotação sexual aumentam a gravidade e vulnerabilidade.
        self.declare(Explanation(
            text="**Fator Agravante (Contexto):** A conduta ocorreu em um local isolado com conotação sexual, o que aumenta a sensação de vulnerabilidade da vítima.",
            source="Fator Adicional"
        ))
        
    @Rule(HistoryFact(history=P(lambda x: x in ["Reincidente", "Frequente"])))
    def explain_history(self):
        # Um histórico de condutas inapropriadas aumenta a gravidade da avaliação.
        self.declare(Explanation(
            text="**Fator Agravante (Histórico):** O agressor possui um histórico de condutas inapropriadas, o que sugere um padrão de comportamento e aumenta a gravidade da situação atual.",
            source="Fator Adicional"
        ))

    @Rule(FrequencyFact(frequency="Repetitivo e/ou Insistente"))
    def explain_frequency(self):
        # Condutas recorrentes são tratadas com mais seriedade.
        self.declare(Explanation(
            text="**Fator Agravante (Frequência):** A conduta é repetitiva e/ou insistente, o que pode criar um ambiente de trabalho hostil continuado e é tratado com mais seriedade.",
            source="Fator Adicional"
        ))

    @Rule(ImpactFact(impact="Negativo intenso"))
    def explain_impact(self):
         # O impacto na vítima é um fator crucial.
        self.declare(Explanation(
            text="**Fator Agravante (Impacto):** A conduta teve um impacto negativo intenso na vítima, causando sofrimento de médio/longo prazo, o que é um forte indicador de gravidade.",
            source="Fator Adicional"
        ))

    @Rule(NonVerbalFact(non_verbal="Agravado"))
    def explain_non_verbal(self):
        # Sinais não-verbais podem intensificar a gravidade.
        self.declare(Explanation(
            text="**Fator Agravante (Sinais Não-Verbais):** A conduta foi acompanhada por sinais não-verbais (linguagem corporal, expressões) que intensificaram sua negatividade, sugerindo ameaça ou desprezo.",
            source="Fator Adicional"
        ))

    @Rule(IntentionFact(intention="Intencional"))
    def explain_intention(self):
        # Condutas intencionais são julgadas mais severamente.
        self.declare(Explanation(
            text="**Fator Agravante (Intenção):** A conduta foi percebida como intencional, com o objetivo claro de causar dano ou desconforto, o que a torna mais grave do que um mal-entendido.",
            source="Fator Adicional"
        ))

    @Rule(HierarchicalRelationFact(relation=P(lambda x: "Superior" in x)))
    def explain_hierarchy(self):
        # A dinâmica de poder, especialmente com superioridade hierárquica, intensifica o impacto.
        self.declare(Explanation(
            text="**Fator Agravante (Hierarquia):** Existe uma relação hierárquica de superioridade do agressor sobre a vítima. Essa dinâmica de poder intensifica o impacto da conduta e a dificuldade da vítima em se defender.",
            source="Fator Adicional"
        ))


    def _get_severity_description(self, level):
        """Auxiliar para obter a descrição do nível de gravidade."""
        descriptions = {
            1: "Em geral, não ofensivo",
            2: "Constrangedor e levemente ofensivo",
            3: "Ofensivo",
            4: "Bastante ofensivo",
            5: "Agressivo e não fisicamente violento",
            6: "Agressivo e fisicamente violento"
        }
        return descriptions.get(level, "Nível desconhecido")