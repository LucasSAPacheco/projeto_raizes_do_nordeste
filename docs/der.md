# DER — Raízes do Nordeste

Diagrama Entidade-Relacionamento do banco de dados da API.

O diagrama abaixo é renderizado automaticamente pelo GitHub e pela maioria dos editores Markdown modernos (VS Code com extensão Mermaid, Obsidian, Typora, etc.).

```mermaid
erDiagram
    USUARIO ||--o{ PEDIDO : "faz"
    USUARIO ||--o| PONTOS_FIDELIDADE : "possui"

    UNIDADE ||--o{ ESTOQUE : "controla"
    UNIDADE ||--o{ PEDIDO : "atende"

    PRODUTO ||--o{ ESTOQUE : "tem saldo em"
    PRODUTO ||--o{ ITEM_PEDIDO : "compoe"

    ESTOQUE ||--o{ MOVIMENTACAO_ESTOQUE : "registra"

    PEDIDO ||--o{ ITEM_PEDIDO : "contem"
    PEDIDO ||--o| PAGAMENTO : "tem"
    PEDIDO ||--o{ HISTORICO_FIDELIDADE : "gera"

    PONTOS_FIDELIDADE ||--o{ HISTORICO_FIDELIDADE : "movimenta"

    USUARIO {
        int id PK
        string nome
        string email UK
        string senha_hash
        enum perfil "ADMIN | GERENTE | ATENDENTE | COZINHA | CLIENTE"
        bool ativo
        bool consentimento_lgpd
        datetime criado_em
    }

    UNIDADE {
        int id PK
        string nome
        string endereco
        string cidade
        string estado
        bool ativa
        datetime criada_em
    }

    PRODUTO {
        int id PK
        string nome
        text descricao
        float preco
        string categoria
        bool disponivel
        datetime criado_em
    }

    ESTOQUE {
        int id PK
        int unidade_id FK
        int produto_id FK
        int quantidade
        datetime atualizado_em
    }

    MOVIMENTACAO_ESTOQUE {
        int id PK
        int estoque_id FK
        enum tipo "ENTRADA | SAIDA"
        int quantidade
        string observacao
        datetime criado_em
    }

    PEDIDO {
        int id PK
        int cliente_id FK
        int unidade_id FK
        enum canal_pedido "APP | TOTEM | BALCAO | PICKUP | WEB"
        enum status "AGUARDANDO_PAGAMENTO | PAGO | EM_PREPARO | PRONTO | ENTREGUE | CANCELADO"
        float valor_total
        text observacao
        datetime criado_em
        datetime atualizado_em
    }

    ITEM_PEDIDO {
        int id PK
        int pedido_id FK
        int produto_id FK
        int quantidade
        float preco_unitario
    }

    PAGAMENTO {
        int id PK
        int pedido_id FK_UK
        string forma_pagamento
        enum status "PENDENTE | APROVADO | RECUSADO"
        float valor
        text resposta_gateway
        datetime criado_em
        datetime atualizado_em
    }

    PONTOS_FIDELIDADE {
        int id PK
        int usuario_id FK_UK
        int saldo
        datetime atualizado_em
    }

    HISTORICO_FIDELIDADE {
        int id PK
        int pontos_id FK
        int pedido_id FK
        string tipo "GANHO | RESGATE"
        int quantidade
        datetime criado_em
    }
```

## Relacionamentos

| De | Para | Cardinalidade | Observação |
|---|---|---|---|
| Usuario | Pedido | 1 : N | Um cliente pode ter vários pedidos |
| Usuario | PontosFidelidade | 1 : 1 | Apenas clientes têm registro de fidelidade |
| Unidade | Estoque | 1 : N | Cada unidade controla seu próprio estoque |
| Unidade | Pedido | 1 : N | Pedido sempre está vinculado a uma unidade |
| Produto | Estoque | 1 : N | Mesmo produto aparece em várias unidades |
| Produto | ItemPedido | 1 : N | Mesmo produto pode aparecer em vários pedidos |
| Estoque | MovimentacaoEstoque | 1 : N | Histórico de entradas e saídas |
| Pedido | ItemPedido | 1 : N | Itens que compõem o pedido |
| Pedido | Pagamento | 1 : 1 | Cada pedido tem no máximo um pagamento |
| Pedido | HistoricoFidelidade | 1 : N | Pedido pode gerar pontos (registro opcional) |
| PontosFidelidade | HistoricoFidelidade | 1 : N | Cada movimentação aparece no histórico |

## Convenções

- **PK** — chave primária
- **FK** — chave estrangeira
- **UK** — chave única
- **FK_UK** — chave estrangeira com restrição de unicidade (relação 1:1)

## Notas de modelagem

- A tabela `estoque` faz a junção produto × unidade. Não há produto solto sem unidade — só existe saldo quando há ao menos uma movimentação naquela unidade.
- O campo `canal_pedido` é obrigatório em `pedidos` (exigência do roteiro) e tem valores fixos via ENUM.
- `pagamento.resposta_gateway` guarda o JSON completo retornado pelo gateway mock, atendendo o requisito de "envio + retorno de status/payload".
- `historico_fidelidade.pedido_id` é nullable porque resgates não estão associados a um pedido.
- `usuario.consentimento_lgpd` registra o aceite explícito (LGPD).
