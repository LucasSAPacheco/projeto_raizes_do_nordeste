# Promoções e Campanhas

Documento de regras (não implementado nesta versão da API). O objetivo é deixar definido como o módulo de promoções deve funcionar quando entrar no escopo, atendendo o requisito do roteiro de "Promoções/campanhas, ao menos como regra/documentação".

## Tipos de promoção previstos

1. **Cupom de desconto** — código que o cliente aplica no pedido. Pode ser percentual (ex.: 10% off) ou valor fixo (ex.: R$ 5 off).
2. **Promoção automática por canal** — descontos aplicados a pedidos feitos por um canal específico (ex.: 5% off em pedidos `APP`).
3. **Combo** — preço promocional para uma combinação fixa de produtos (ex.: tapioca + suco por R$ 18).
4. **Campanha por unidade** — desconto vinculado a uma unidade específica em datas determinadas (ex.: aniversário da loja).

## Regras gerais

- Toda promoção tem **data de início** e **data de fim**.
- Toda promoção tem um **status** (`ATIVA`, `INATIVA`, `EXPIRADA`).
- Cupons têm **limite de uso** total e **limite por cliente**.
- O desconto é aplicado sobre o `valor_total` do pedido **antes** da etapa de pagamento.
- Promoções não acumulam: o pedido aplica a de **maior desconto** quando há concorrência.
- Pedido cancelado libera o uso do cupom de volta.

## Como se encaixaria no modelo atual

Sem alterar o que já existe, seria necessário:

- Nova tabela `promocoes` (`id`, `tipo`, `codigo`, `valor`, `percentual`, `data_inicio`, `data_fim`, `unidade_id` opcional, `canal_pedido` opcional, `status`, `limite_total`, `limite_por_cliente`).
- Nova tabela `pedido_promocao` (relação N:N entre `pedidos` e `promocoes`, registrando o desconto aplicado).
- Campo `desconto` em `pedidos` (float, default 0) e `valor_final` calculado como `valor_total - desconto`.
- Endpoint `POST /pedidos/{id}/cupom` para o cliente aplicar um cupom antes do pagamento.
- Endpoints administrativos `/promocoes` (CRUD restrito a `ADMIN` / `GERENTE`).

## Observações de segurança

- Cupom é validado no servidor (cliente nunca informa o desconto, apenas o código).
- Aplicação de cupom é idempotente por pedido (só pode aplicar uma vez).
- Tentativas de aplicar cupom inválido ou expirado são logadas para detectar abuso.
