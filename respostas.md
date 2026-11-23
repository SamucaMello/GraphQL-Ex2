# Respostas – Catálogo de Livros com GraphQL

## Parte 1: Reflexão

**1. Por que status é melhor como enum do que como String?**
O enum limita o campo aos três valores válidos (WANT_TO_READ, READING, FINISHED) e o próprio schema rejeita qualquer outro valor antes de chegar ao resolver. Com String, "lendo", "Reading" ou um erro de digitação passariam, e o código teria que validar tudo na mão. Ainda ganha autocomplete e documentação no GraphiQL.

**2. Por que rating é opcional e title não?**
Todo livro tem título, um livro sem título não faz sentido, então o campo é obrigatório (`String!`). Já a nota só existe depois que o livro foi lido: antes disso a ausência de nota é um estado válido, e o `null` representa isso melhor do que um valor falso como 0.

**3. bookCount deve ser armazenado ou calculado por um resolver?**
Calculado. Ele é derivado da lista de livros do autor, então guardar o número criaria dois lugares com a mesma informação, e seria preciso atualizar o contador em todo addBook e deleteBook, com risco de ficar inconsistente. Calculando no resolver, o valor está sempre correto e só é executado quando o cliente pede o campo.

## Parte 4: Análise

**9. Quantas requisições em REST? E em GraphQL?**
Em REST seriam no mínimo 3 (livros, autores e estatísticas), e mais uma por livro se o autor vier só como id. No GraphQL fiz 1: a query `Tela` busca `books`, `authors` e `stats` juntas, e ainda traz `author { name }` dentro de cada livro.

**10. O que acontece quando uma mutation lança um erro?**
No Strawberry a resposta continua com HTTP 200 (testei com `rateBook(id: 1, rating: 9)`). O corpo vem com `"data": null` e uma lista `errors` com a mensagem e o `path` da mutation. Por isso o front não pode confiar só em `res.ok`: a função `gql()` também verifica `json.errors` e lança um Error com a mensagem.

**11. O que é o problema N+1 e como o DataLoader ajuda?**
Buscar 100 autores é 1 consulta, e se `Author.books` faz uma consulta ao banco por autor, são mais 100: 101 no total (N+1). O DataLoader junta todos os ids pedidos no mesmo ciclo de execução e faz uma única consulta (`WHERE author_id IN (...)`), reduzindo para 2 consultas.

**12. Vantagem e desvantagem de um único endpoint**
Vantagem: o front conhece uma única URL e pede exatamente os campos de que precisa, sem criar endpoint novo a cada tela. Desvantagem: cache HTTP, métricas e rate limit por rota ficam mais difíceis, já que tudo é POST para /graphql e os erros voltam com status 200.
