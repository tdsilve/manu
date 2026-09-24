# Manu

Assistente que responde dúvidas sobre um eletrodoméstico com base no manual oficial do fabricante, citando a página. O produto é identificado pela foto da etiqueta; a garantia é só um dos assuntos possíveis, não um requisito.

## Language

### Produto

**Etiqueta de identificação**:
A plaqueta fixada no aparelho com marca, código do modelo e número de série; é o que o usuário fotografa.
_Avoid_: Etiqueta do produto, plaqueta, selo

**Código do modelo**:
O identificador do fabricante que distingue um modelo de aparelho (ex.: o texto impresso no campo "Modelo" da etiqueta); liga o produto ao manual.
_Avoid_: Modelo (sozinho), SKU, referência

**Identificação do produto**:
O passo que determina marca e código do modelo, a partir da foto da etiqueta ou do código digitado pelo usuário.
_Avoid_: Reconhecimento, detecção

### Manuais

**Manual**:
Documento oficial publicado pelo fabricante para um ou mais códigos de modelo.
_Avoid_: Guia, documentação, PDF

**Base de manuais**:
O conjunto de manuais já indexados que o Manu consegue consultar.
_Avoid_: Knowledge base, acervo, banco

**Busca de manual**:
Obtenção automática, no site do fabricante, do manual de um modelo que não está na base de manuais. Melhoria futura; só acontece quando a base não tem o manual.
_Avoid_: Scraping, crawler, download

**Modelo sem manual**:
Um código do modelo identificado para o qual a base de manuais não tem manual; fica registrado para orientar o que adicionar (e, no futuro, disparar a busca de manual).
_Avoid_: Miss, pedido pendente

### Consulta

**Produto selecionado**:
O produto identificado e confirmado pelo usuário; as perguntas seguintes são respondidas só com os manuais dele, até o usuário trocar de produto.
_Avoid_: Produto atual, contexto, sessão
