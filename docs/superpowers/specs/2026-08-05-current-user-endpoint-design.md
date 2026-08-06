# Dados do usuário autenticado

## Objetivo

Disponibilizar `GET /api/v1/users/me/` e `PATCH /api/v1/users/me/` para que um usuário autenticado por JWT consulte seus dados públicos e atualize parcialmente apenas `first_name` e `last_name`.

## Arquitetura

Será criado um `CurrentUserSerializer` dedicado. Ele representará somente `id`, `email`, `first_name` e `last_name`; `id` e `email` serão somente leitura. A validação rejeitará payload vazio, dados que não sejam objetos JSON e qualquer campo diferente dos dois nomes atualizáveis. Os nomes reutilizarão `StrictCharField`, aceitarão strings vazias e terão limite de 150 caracteres.

Uma `CurrentUserView` baseada em `APIView` declarará `IsAuthenticated`. O `GET` serializará `request.user`. O `PATCH` usará o mesmo usuário como instância, `partial=True`, validará, salvará e devolverá os dados públicos atualizados. Nenhum identificador será recebido ou consultado.

A URL será registrada em `apps/accounts/urls.py` como `users/me/`. Modelos, migrations, configurações e dependências não serão alterados.

## Erros e segurança

Requisições sem autenticação serão recusadas pelo JWT com `401`. Payload vazio, campos desconhecidos ou campos imutáveis retornarão `400`. A validação ocorrerá antes de salvar, impedindo atualização parcial quando houver qualquer campo proibido. Métodos não implementados continuarão retornando `405` pelo DRF.

## Testes

O escopo solicitado terá exatamente dois testes por rota:

- GET com access token válido retorna `200` e exatamente os quatro campos públicos do usuário.
- GET sem token retorna `401`.
- PATCH com access token válido atualiza e persiste parcialmente um nome, preservando o campo omitido e o e-mail.
- PATCH autenticado com campo proibido retorna `400` e não aplica nenhuma alteração do payload.

Os tokens usados nos cenários autenticados serão obtidos pelo endpoint real de login. Ao final serão executados esses testes, a suíte existente, `manage.py check` e a verificação de migrations.

## Documentação

O README receberá exemplos de GET e PATCH, indicação de JWT obrigatório, campos editáveis, imutabilidade do e-mail e respostas esperadas para payload vazio ou autenticação inválida.
