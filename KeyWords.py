# Palavras-chave e frases para cada Nível de Gravidade
# Estas serão usadas pelo Gemini para identificar o nível base da conduta.

KEYWORDS_NIVEL_1 = [        
    "comentários sobre corte de cabelo",
    "elogios por roupa nova",
    "discussões sobre clima",
    "assuntos neutros",
    "interações cotidianas",
    "comportamento socialmente aceitável",
    "não ofensivo",
]

KEYWORDS_NIVEL_2 = [
    "perguntas sobre habilidades de trabalho baseadas em estereótipos de gênero",
    "comentários sobre aptidão física de grupos étnicos",
    "comentários sobre aparência de grupos étnicos",
    "criação de desconforto",
    "embaraço",
    "desrespeitoso ou insensível",
    "evocam estereótipos sutis",
    "levemente ofensivo",
]

KEYWORDS_NIVEL_3 = [
    "piadas sobre orientação sexual",
    "insinuações sobre orientação sexual",
    "apelidos pejorativos raciais",
    "apelidos pejorativos de gênero",
    "retirar oportunidades de trabalho por gênero",
    "falta de consideração pelas diferenças",
    "reforçam negativamente estereótipos",
    "reproduzem estruturas de privilégio",
    "ofensivo",
]

KEYWORDS_NIVEL_4 = [
    "insultos diretos",
    "insultos ostensivos",
    "comentários depreciativos sobre capacidade intelectual",
    "humilhação maliciosa",
    "ridicularização maliciosa",
    "imitação ofensiva de sotaque",
    "toques não solicitados",
    "explicitamente humilhantes",
    "degradantes",
    "intencionais",
    "objetivo de insultar ou diminuir",
    "bastante ofensivo",
]

KEYWORDS_NIVEL_5 = [
    "avanços sexuais não solicitados",
    "comentários racistas",
    "compartilhamento de material pornográfico",
    "armazenamento de material pornográfico",
    "sugestão de retaliação sexual",
    "ações persistentes baseadas em gênero",
    "ações persistentes baseadas em raça",
    "ações persistentes baseadas em sexualidade",
    "cria ambiente hostil",
    "intimidador",
    "agressivo e não fisicamente violento",
]

KEYWORDS_NIVEL_6 = [
    "agressões físicas",
    "ameaças de violência grave",
    "coerção que coloque em risco a segurança física",
    "ameaça direta à integridade física",
    "agressivo e fisicamente violento",
]

# Dicionário mapeando as palavras-chave aos seus respectivos níveis.
# Isso será útil para o prompt do Gemini e para declarar fatos.
ALL_KEYWORDS_MAPPING = {
    "Nível 1": KEYWORDS_NIVEL_1,
    "Nível 2": KEYWORDS_NIVEL_2,
    "Nível 3": KEYWORDS_NIVEL_3,
    "Nível 4": KEYWORDS_NIVEL_4,
    "Nível 5": KEYWORDS_NIVEL_5,
    "Nível 6": KEYWORDS_NIVEL_6,
}