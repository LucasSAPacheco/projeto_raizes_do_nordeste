"""criacao_inicial_das_tabelas

Revision ID: 001
Revises: 
Create Date: 2026-05-09

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela de usuários
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=150), nullable=False),
        sa.Column('senha_hash', sa.String(length=255), nullable=False),
        sa.Column('perfil', sa.Enum('ADMIN', 'GERENTE', 'ATENDENTE', 'COZINHA', 'CLIENTE', name='perfil_usuario'), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=True),
        sa.Column('consentimento_lgpd', sa.Boolean(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=True)
    op.create_index(op.f('ix_usuarios_id'), 'usuarios', ['id'], unique=False)

    # Tabela de unidades
    op.create_table(
        'unidades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('endereco', sa.String(length=255), nullable=False),
        sa.Column('cidade', sa.String(length=100), nullable=False),
        sa.Column('estado', sa.String(length=2), nullable=False),
        sa.Column('ativa', sa.Boolean(), nullable=True),
        sa.Column('criada_em', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_unidades_id'), 'unidades', ['id'], unique=False)

    # Tabela de produtos
    op.create_table(
        'produtos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('preco', sa.Float(), nullable=False),
        sa.Column('categoria', sa.String(length=50), nullable=False),
        sa.Column('disponivel', sa.Boolean(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_produtos_id'), 'produtos', ['id'], unique=False)

    # Tabela de estoque (produto x unidade)
    op.create_table(
        'estoque',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('produto_id', sa.Integer(), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['produto_id'], ['produtos.id']),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_estoque_id'), 'estoque', ['id'], unique=False)

    # Tabela de movimentações de estoque
    op.create_table(
        'movimentacoes_estoque',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('estoque_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.Enum('ENTRADA', 'SAIDA', name='tipo_movimentacao_estoque'), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('observacao', sa.String(length=255), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['estoque_id'], ['estoque.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_movimentacoes_estoque_id'), 'movimentacoes_estoque', ['id'], unique=False)

    # Tabela de pedidos
    op.create_table(
        'pedidos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('unidade_id', sa.Integer(), nullable=False),
        sa.Column('canal_pedido', sa.Enum('APP', 'TOTEM', 'BALCAO', 'PICKUP', 'WEB', name='canal_pedido'), nullable=False),
        sa.Column('status', sa.Enum('AGUARDANDO_PAGAMENTO', 'PAGO', 'EM_PREPARO', 'PRONTO', 'ENTREGUE', 'CANCELADO', name='status_pedido'), nullable=False),
        sa.Column('valor_total', sa.Float(), nullable=False),
        sa.Column('observacao', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.Column('atualizado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['unidade_id'], ['unidades.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pedidos_id'), 'pedidos', ['id'], unique=False)

    # Tabela de itens do pedido
    op.create_table(
        'itens_pedido',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('produto_id', sa.Integer(), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('preco_unitario', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id']),
        sa.ForeignKeyConstraint(['produto_id'], ['produtos.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_itens_pedido_id'), 'itens_pedido', ['id'], unique=False)

    # Tabela de pagamentos
    op.create_table(
        'pagamentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('forma_pagamento', sa.String(length=50), nullable=False),
        sa.Column('status', sa.Enum('PENDENTE', 'APROVADO', 'RECUSADO', name='status_pagamento'), nullable=False),
        sa.Column('valor', sa.Float(), nullable=False),
        sa.Column('resposta_gateway', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.Column('atualizado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pedido_id'),
    )
    op.create_index(op.f('ix_pagamentos_id'), 'pagamentos', ['id'], unique=False)

    # Tabela de pontos de fidelidade
    op.create_table(
        'pontos_fidelidade',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('saldo', sa.Integer(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('usuario_id'),
    )
    op.create_index(op.f('ix_pontos_fidelidade_id'), 'pontos_fidelidade', ['id'], unique=False)

    # Tabela de histórico de fidelidade
    op.create_table(
        'historico_fidelidade',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pontos_id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=True),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('quantidade', sa.Integer(), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedidos.id']),
        sa.ForeignKeyConstraint(['pontos_id'], ['pontos_fidelidade.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_historico_fidelidade_id'), 'historico_fidelidade', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_historico_fidelidade_id'), table_name='historico_fidelidade')
    op.drop_table('historico_fidelidade')
    op.drop_index(op.f('ix_pontos_fidelidade_id'), table_name='pontos_fidelidade')
    op.drop_table('pontos_fidelidade')
    op.drop_index(op.f('ix_pagamentos_id'), table_name='pagamentos')
    op.drop_table('pagamentos')
    op.drop_index(op.f('ix_itens_pedido_id'), table_name='itens_pedido')
    op.drop_table('itens_pedido')
    op.drop_index(op.f('ix_pedidos_id'), table_name='pedidos')
    op.drop_table('pedidos')
    op.drop_index(op.f('ix_movimentacoes_estoque_id'), table_name='movimentacoes_estoque')
    op.drop_table('movimentacoes_estoque')
    op.drop_index(op.f('ix_estoque_id'), table_name='estoque')
    op.drop_table('estoque')
    op.drop_index(op.f('ix_produtos_id'), table_name='produtos')
    op.drop_table('produtos')
    op.drop_index(op.f('ix_unidades_id'), table_name='unidades')
    op.drop_table('unidades')
    op.drop_index(op.f('ix_usuarios_email'), table_name='usuarios')
    op.drop_index(op.f('ix_usuarios_id'), table_name='usuarios')
    op.drop_table('usuarios')
    op.execute('DROP TYPE IF EXISTS perfil_usuario')
    op.execute('DROP TYPE IF EXISTS canal_pedido')
    op.execute('DROP TYPE IF EXISTS status_pedido')
    op.execute('DROP TYPE IF EXISTS status_pagamento')
    op.execute('DROP TYPE IF EXISTS tipo_movimentacao_estoque')
