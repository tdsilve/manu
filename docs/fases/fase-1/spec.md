# Fase 1 — RAG básico: perguntas sobre manuais com citação de página

**Status:** ready-for-agent

## Problem Statement

Quem tem uma geladeira ou um micro-ondas com algum problema raramente ainda tem o manual em mãos. Mesmo quando encontra o PDF no site do fabricante, precisa folhear dezenas de páginas para descobrir se aquele comportamento é normal, como resolver, como usar ou limpar corretamente, ou o que a garantia cobre. O resultado é ligar para a assistência técnica sem necessidade, usar o aparelho de forma errada, ou deixar de acionar uma garantia que existia.

Do ponto de vista da autora (projeto de portfólio, migração de frontend para engenharia de IA): falta um primeiro pipeline de RAG funcionando de ponta a ponta, construído sem framework, com avaliação mensurável, que sirva de base para as 7 fases seguintes.

## Solution

O Manu responde perguntas em linguagem do dia a dia sobre geladeiras e micro-ondas Electrolux e Brastemp, usando apenas o conteúdo dos manuais oficiais. Toda resposta mostra de onde veio: o trecho do manual destacado, o nome do manual e a página. Quando os manuais não trazem a resposta, o Manu diz claramente que não sabe, em vez de inventar.

Na Fase 1:

- 15 a 20 manuais baixados à mão são indexados localmente (texto extraído por página, embeddings locais com Ollama, ChromaDB).
- Uma API (FastAPI) expõe `POST /ask`: busca as 3 páginas mais parecidas com a pergunta; se nenhuma passar do limiar de similaridade, recusa sem chamar o LLM; se passar, pede ao Claude uma resposta restrita ao contexto, com citações.
- Uma interface web simples (Next.js) permite perguntar e ver resposta, trechos citados e páginas, com a similaridade disponível em "ver detalhes".
- Um gabarito escrito à mão e um script de avaliação medem a qualidade da busca e a taxa de recusa correta, e fornecem a distribuição de similaridades para calibrar o limiar.

## User Stories

### Usuário final

1. Como dono de uma geladeira, quero digitar minha dúvida com as minhas palavras ("a geladeira está fazendo barulho de água"), para não ter que conhecer os termos técnicos do manual.
2. Como dono de um micro-ondas, quero perguntar o que significa um código de erro que apareceu no visor, para saber se é algo que eu mesmo resolvo.
3. Como usuário, quero receber uma resposta curta e direta, para não ter que ler o manual inteiro.
4. Como usuário, quero ver o trecho do manual que embasa a resposta, para confiar que ela não foi inventada.
5. Como usuário, quero ver o nome do manual (marca e modelo) e a página citada, para poder conferir no manual original se quiser.
6. Como usuário, quero ver mais de uma citação quando a resposta vier de mais de uma página, para entender o contexto completo.
7. Como usuário, quero que o Manu diga claramente quando os manuais não têm a resposta, para não seguir uma orientação inventada.
8. Como usuário, quero que a recusa me sugira um próximo passo (por exemplo, procurar a assistência técnica), para não ficar sem saída.
9. Como usuário, quero perguntar se um problema está coberto pela garantia, para decidir se aciono o fabricante.
10. Como usuário, quero saber o prazo de garantia que o manual informa, para saber se ainda estou dentro dele.
11. Como usuário, quero saber o que o manual diz que invalida a garantia, para não perder a cobertura sem querer.
12. Como usuário, quero perguntar sobre instalação, limpeza e uso correto, para resolver dúvidas do dia a dia além de defeitos.
13. Como usuário, quero ver um indicador de "carregando" enquanto a resposta é gerada, para saber que o sistema está trabalhando.
14. Como usuário, quero ver uma mensagem de erro compreensível se algo falhar, para saber que devo tentar de novo e não achar que a resposta é "não sei".
15. Como usuário, quero que o botão de enviar fique desabilitado com a pergunta vazia, para não enviar perguntas em branco por engano.
16. Como usuário curioso, quero abrir "ver detalhes" em cada citação e ver a similaridade, para entender o quanto o trecho combina com a minha pergunta.
17. Como usuário, quero fazer uma nova pergunta sem recarregar a página, para tirar várias dúvidas seguidas.
18. Como usuário, quero que a resposta venha em português, para entender sem esforço.

### Autora / desenvolvedora

19. Como desenvolvedora, quero extrair o texto de um manual página por página e salvá-lo, para conferir manualmente contra o PDF original antes de construir o resto do pipeline.
20. Como desenvolvedora, quero registrar cada manual em uma lista (marca, modelo, categoria, link de origem, arquivo local), para que qualquer pessoa consiga baixar os mesmos manuais sem que os PDFs fiquem no repositório público.
21. Como desenvolvedora, quero rodar um único comando que indexe todos os manuais da lista, para montar a base de conhecimento do zero.
22. Como desenvolvedora, quero que indexar de novo o mesmo manual substitua os dados anteriores em vez de duplicar, para poder reindexar sem medo.
23. Como desenvolvedora, quero que páginas sem texto (capas, páginas só com imagem) sejam ignoradas e contadas no log, para não poluir a base e saber quanto conteúdo ficou de fora.
24. Como desenvolvedora, quero que cada trecho indexado guarde marca, modelo, categoria, nome do manual e número da página, para montar citações precisas.
25. Como desenvolvedora, quero trocar o modelo de embeddings e o modelo do Claude por configuração, para experimentar sem mexer no código.
26. Como desenvolvedora, quero que o limiar de similaridade e o top-k sejam configuráveis, para calibrá-los a partir dos dados.
27. Como desenvolvedora, quero que perguntas abaixo do limiar sejam recusadas sem chamar o Claude, para economizar custo e reduzir alucinação.
28. Como desenvolvedora, quero que o prompt do Claude proíba responder fora do contexto fornecido e exija citar as páginas usadas, para ter uma segunda barreira contra alucinação.
29. Como desenvolvedora, quero que a resposta da API diga explicitamente se foi uma recusa, para a interface e a avaliação tratarem esse caso sem interpretar texto.
30. Como desenvolvedora, quero que a chave da API do Claude fique em `.env` (fora do git) com um `.env.example` versionado, para nunca vazar segredos no repositório público.
31. Como desenvolvedora, quero escrever um gabarito de perguntas em linguagem leiga com a resposta esperada (manual e página), para medir a qualidade de forma objetiva.
32. Como desenvolvedora, quero incluir no gabarito 3 ou 4 perguntas que os manuais não respondem, para medir a taxa de recusa correta.
33. Como desenvolvedora, quero rodar um script de avaliação que passe cada pergunta do gabarito pelo pipeline real, para ver as páginas recuperadas, as similaridades e a resposta gerada.
34. Como desenvolvedora, quero que a avaliação calcule se a página esperada apareceu entre as 3 recuperadas, para medir a busca separadamente da geração.
35. Como desenvolvedora, quero que a avaliação mostre a distribuição de similaridades das perguntas com resposta e das sem resposta, para escolher o limiar com base em dados.
36. Como desenvolvedora, quero que a avaliação gere um relatório fácil de ler, para julgar manualmente cada resposta na Fase 1.
37. Como desenvolvedora, quero testes automáticos do `POST /ask` que não dependam de Ollama nem do Claude, para rodá-los rápido, sem custo e sem rede.
38. Como desenvolvedora, quero testes da extração de PDF com um PDF de teste pequeno criado por nós, para validar a etapa mais arriscada sem versionar manuais de terceiros.
39. Como desenvolvedora, quero rodar API e web localmente com instruções claras no README, para que recrutadores e eu mesma consigam reproduzir o projeto.
40. Como recrutador avaliando o portfólio, quero ver no README o que foi construído, como foi avaliado e os números obtidos, para entender a competência demonstrada.

## Implementation Decisions

### Estrutura

- Monorepo com duas partes: a API em Python (pipeline RAG e FastAPI) e a interface web em Next.js.
- Nenhum framework de RAG (LangChain, LlamaIndex etc.): cada etapa é construída com peças soltas, para fins de aprendizado.

### Manuais e dados

- Os manuais são baixados à mão (sem scraping automatizado, por causa dos termos de uso dos fabricantes).
- Um arquivo de registro versionado lista cada manual: identificador, marca, modelo(s), categoria (geladeira / micro-ondas), link de origem e nome do arquivo local esperado.
- Os PDFs ficam em uma pasta local ignorada pelo git. A base do ChromaDB também fica fora do git e é regenerada pelo comando de indexação.
- Todos os arquivos de ambiente (`.env`) são ignorados pelo git; só o `.env.example` é versionado.

### Módulos da API

- **Extração:** recebe um PDF e devolve uma lista de páginas (número da página a partir de 1, texto). Usa pdfplumber. Normaliza espaços em branco; páginas sem texto útil são descartadas e contadas. Também consegue salvar o texto por página em disco, para a conferência manual do primeiro PR.
- **Indexação:** lê o registro de manuais, extrai cada um, gera embeddings via Ollama e grava no ChromaDB. Um trecho equivale a uma página (chunking por página). O identificador de cada trecho é `manual + página`, então reindexar substitui em vez de duplicar. Os metadados de cada trecho são: identificador do manual, marca, modelo, categoria e página.
- **Busca:** gera o embedding da pergunta (mesmo modelo da indexação), consulta o ChromaDB com top-k = 3 e converte a distância em similaridade (quanto maior, mais parecido), para facilitar o limiar e a leitura na interface.
- **Geração:** monta o prompt com as páginas recuperadas (cada uma rotulada com manual e página) e chama o Claude. O prompt instrui: responder apenas com base nos trechos, em português, de forma curta; indicar quais trechos foram usados; e, se os trechos não bastarem, sinalizar recusa de forma estruturada, sem depender de texto livre.
- **Orquestração do `/ask`:** busca → se a melhor similaridade estiver abaixo do limiar, retorna recusa sem chamar o Claude → senão, gera → retorna resposta e citações.
- Embedder, cliente do Claude e armazenamento vetorial são dependências injetadas na orquestração, o que permite substituí-las por versões falsas nos testes.

### Configuração (variáveis de ambiente)

- Chave da API do Claude e modelo do Claude.
- URL do Ollama e modelo de embeddings (deve ser multilíngue, porque manuais e perguntas estão em português).
- Local da base do ChromaDB e da pasta de PDFs.
- top-k (padrão 3) e limiar de similaridade (valor inicial provisório, recalibrado com a avaliação).
- Origem permitida para CORS (a URL da interface web).

### Contrato da API

`POST /ask`

- Requisição: `{ "question": string }`. A pergunta é obrigatória, sem espaços nas pontas e com tamanho máximo razoável (ex.: 1000 caracteres). Pergunta vazia ou longa demais retorna 422.
- Resposta 200:
  - `answer`: string (a resposta, ou a mensagem de recusa com sugestão de próximo passo)
  - `refused`: boolean
  - `citations`: lista de `{ manual_id, brand, model, page, excerpt, similarity }`. Vazia quando `refused` é true por limiar; quando o Claude responde, contém só os trechos que ele indicou ter usado.
- Falha do Ollama ou do Claude retorna 502 ou 503 com mensagem genérica, nunca uma recusa disfarçada. Os detalhes vão para o log do servidor.
- `GET /health` para checar se a API está no ar.

### Interface web (Next.js)

- Uma página: campo de pergunta, botão enviar (desabilitado com o campo vazio ou durante o carregamento), estado de carregamento e estado de erro.
- Resultado: texto da resposta; para cada citação, um cartão com marca, modelo, página e o trecho com as partes mais relevantes destacadas. Em "ver detalhes" aparece a similaridade.
- Recusa: exibida de forma distinta (não como erro), com a sugestão de próximo passo.
- Visual simples e funcional nesta fase.

### Avaliação

- Gabarito versionado, escrito à mão pela autora: cada item tem a pergunta, a categoria e o manual e as páginas esperadas, ou a marcação "sem resposta". Inclui 3 ou 4 perguntas sem resposta nos manuais.
- Script de avaliação executado manualmente: roda cada pergunta pelo pipeline real (Ollama, ChromaDB e Claude de verdade) e gera um relatório com páginas recuperadas, similaridades, resposta e recusa.
- Métricas: acerto de busca (a página esperada está entre as top-3), taxa de recusa correta (perguntas sem resposta que foram recusadas) e taxa de recusa indevida (perguntas com resposta que foram recusadas).
- O relatório mostra a distribuição das melhores similaridades, separada entre perguntas com e sem resposta, para calibrar o limiar.
- O julgamento da qualidade da resposta gerada é manual nesta fase: o relatório tem espaço para a autora anotar certo/errado.

## Testing Decisions

- **O que é um bom teste aqui:** verifica comportamento externo (o que entra e o que sai de um ponto de entrada público), nunca detalhes internos como a formatação exata do prompt ou chamadas a funções privadas. Um teste deve continuar passando se a implementação interna for refeita.
- **Ponto de teste 1: `POST /ask`** (o principal). Os testes chamam a API por HTTP em processo e usam:
  - um embedder falso e determinístico (vetores escolhidos para controlar quais páginas ficam parecidas com a pergunta);
  - um cliente falso do Claude (devolve respostas pré-definidas e registra se foi chamado);
  - um ChromaDB real e temporário, populado pelo próprio caminho de indexação.

  Casos cobertos: pergunta com resposta retorna `answer`, `refused=false` e citações com marca, modelo, página, trecho e similaridade; melhor similaridade abaixo do limiar retorna recusa **sem** chamar o Claude; o Claude sinalizando recusa retorna `refused=true`; citações incluem só os trechos usados; pergunta vazia ou longa demais retorna 422; falha do embedder ou do Claude retorna erro 5xx e não recusa; reindexar o mesmo manual não duplica resultados.
- **Ponto de teste 2: extração de PDF.** Usa um PDF de teste pequeno criado pelo projeto (conteúdo próprio, pode ser público), com páginas de texto conhecido e uma página em branco. Verifica número de páginas, numeração a partir de 1, texto de cada página e descarte da página sem texto.
- **Fora dos testes automáticos:** o script de avaliação (usa serviços reais e manuais que não estão no repositório) e a interface web nesta fase.
- **Prior art:** nenhum. O repositório ainda não tem código; estes serão os primeiros testes e servirão de modelo para as próximas fases.
- Os testes rodam sem rede, sem Ollama e sem chave da API do Claude.

## Out of Scope

- Foto da etiqueta do produto e extração do código/modelo por imagem.
- Foto do defeito ou qualquer entrada por imagem.
- Upload de nota fiscal e validação de data de compra.
- Filtrar a busca por marca ou modelo do usuário (fica para a Fase 2, identificação por código digitado).
- Chunking diferente de "uma página" e reranking.
- OCR ou modelo de visão para PDFs escaneados.
- Memória de conversa e perguntas de acompanhamento.
- SQL, APIs externas e agente (incluindo buscar manuais no site do fabricante).
- LLM como juiz e avaliação automatizada via GitHub Actions.
- Comparação com LLM local via Ollama para a geração.
- Identidade visual de produto na interface.
- Categorias além de geladeira e micro-ondas e marcas além de Electrolux e Brastemp.
- Deploy público.

## Further Notes

- **Primeiro PR planejado:** somente a extração (ponto de teste 2 e o salvamento do texto por página), com conferência manual de 1 manual contra o PDF original, antes de embeddings, ChromaDB ou LLM. Isso valida a etapa mais arriscada.
- **Conteúdo extraído e repositório público:** o contexto permite publicar o "conteúdo indexado", mas não os PDFs. Esta spec mantém fora do git tanto os PDFs quanto a base do ChromaDB e os textos extraídos; o que é versionado é o registro de manuais com links de origem. Se no futuro fizer sentido publicar texto extraído, vale revisar os termos de uso de cada fabricante antes.
- **Limiar de similaridade:** comece com um valor provisório e ajuste depois da primeira avaliação, olhando onde as distribuições de perguntas com e sem resposta se separam. Registre o valor escolhido e o motivo no README.
- **Modelo de embeddings:** precisa lidar bem com português. A escolha exata fica para a implementação, mas deve ser registrada (com o motivo) junto com os resultados da avaliação.
- **Segurança do repositório público:** o `.gitignore` deve cobrir `.env`, a pasta de PDFs, a base do ChromaDB e os textos extraídos antes do primeiro commit de código.
- O arquivo de contexto do projeto (`context.md`) está na raiz, mas ainda não foi versionado.
