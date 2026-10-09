# Manuais versionados no repositório

**Revisado em 2026-10-07.** A decisão original mantinha os PDFs fora do git, porque pertencem aos fabricantes e não são redistribuídos. Foi revista: os PDFs de `api/data/pdfs/` passam a ser versionados, para que o deploy e qualquer clone tenham os mesmos manuais sem depender de download à mão.

Os manuais são públicos nos sites dos fabricantes, mas os termos de uso de cada um não foram conferidos quanto à redistribuição. O risco aceito é um pedido de remoção, de baixa consequência. Como o repositório é público, um PDF commitado fica no histórico mesmo se for apagado depois; para removê-lo seria preciso reescrever o histórico.

A base vetorial (`api/data/chroma/`), os textos extraídos e os relatórios de avaliação continuam fora do git. O registro de manuais mantém os links de origem.
