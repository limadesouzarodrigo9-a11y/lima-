# Centralized messages for the bot to allow easy editing and localization

MESSAGES = {
    "despertar": {
        "title": "Olá 🙃",
        "description": "Configure seu servidor aqui!",
        "buttons": {
            "start": "🚀 Iniciar"
        }
    },
    "terms_of_use": {
        "title": "📜 Termos de Uso",
        "description": (
            "Ao utilizar o bot de vendas e realizar compras por meio do servidor, "
            "o usuário declara estar ciente e de acordo com os presentes Termos de Uso.\n\n"
            "**1. Descontos**\n"
            "Poderão ser concedidos descontos no valor de R$ 5,00 até R$ 10,00, "
            "conforme as condições estabelecidas pela administração.\n\n"
            "O desconto poderá ser aplicado uma vez por mês, conforme a disponibilidade "
            "e as regras definidas pela administração.\n\n"
            "O desconto deverá ser aplicado no momento da compra e ficará vinculado "
            "à respectiva transação.\n\n"
            "Os descontos não são cumulativos, salvo quando expressamente autorizado pela administração.\n\n"
            "**2. Responsabilidade pela entrega**\n"
            "A concessão de um desconto não isenta o vendedor da obrigação de entregar o produto adquirido.\n\n"
            "Após a confirmação da compra, o produto deverá ser entregue ao comprador normalmente, "
            "respeitando as condições da venda.\n\n"
            "Caso o vendedor se recuse injustificadamente a entregar o produto após a realização da compra, "
            "poderão ser aplicadas medidas administrativas, incluindo banimento do servidor, conforme a gravidade da situação.\n\n"
            "**3. Penalidades**\n"
            "O descumprimento das regras poderá resultar em medidas administrativas, incluindo:\n"
            "- Advertência;\n"
            "- Suspensão ou restrição de acesso aos recursos de venda;\n"
            "- Banimento do servidor;"
        ),
        "button_accept": "Li e Aceito os Termos",
        "wait_message": "⚠️ Por favor, aguarde 15 segundos antes de aceitar os termos."
    },

    "server_pre_ready": {
        "pix_modal": {
            "title": "🔑 Cadastro de Chave Pix",
            "pix_key_label": "Chave Pix",
            "pix_key_placeholder": "Insira sua chave Pix aqui...",
            "pix_type_label": "Tipo de Chave",
            "pix_type_placeholder": "CPF, Email, Telefone ou Aleatória..."
        },
        "success_title": "Servidor Pré-Pronto Criado! ✅",
        "success_description": "A estrutura do servidor foi criada com sucesso. Alguns canais podem precisar de ajustes finais de permissões."
    },
    "shop": {
        "admin_panel": {
            "title": "🛒 Painel da Loja",
            "description": "Gerencie seus produtos e vendas através do menu abaixo."
        },
        "product_embed": {
            "title": "📦 {product_name}",
            "description": "{description}\n\n**Preço:** R$ {price}\n**Estoque:** {stock}\n**Duração:** {duration}",
            "button_buy": "🛒・Compre"
        },
        "purchase_flow": {
            "variant_select": "Escolha uma opção de plano:",
            "order_title": "🛒 PEDIDO",
            "order_description": "Produto: {product}\nPlano: {variant}\nValor: R$ {amount}\n\nStatus: Aguardando pagamento\n\nChave Pix:\n`{pix_key}`",
            "confirm_button": "💰 Confirmar Compra",
            "copy_button": "📋 Copiar Chave Pix",
            "no_permission": "⚠️ Você não possui permissão para confirmar este pagamento. Aguarde um administrador."
        },
        "confirmed": {
            "title": "✅ Pagamento Confirmado!",
            "description": "Seu pedido **{order_id}** foi confirmado.\nProduto: {product}\nValor: R$ {amount}"
        },
        "post_purchase": {
            "dm_title": "📦 Compra Confirmada!",
            "dm_description": "Olá! Seu pagamento foi confirmado com sucesso. Por favor, volte ao servidor e abra um ticket de atendimento para receber seu produto.",
            "feedback_title": "⭐ Sua opinião é importante!",
            "feedback_description": "Agora que sua compra foi concluída, gostaríamos de saber o que achou. Clique no botão abaixo para deixar seu feedback!",
            "feedback_button": "Deixar feedback"
        }
    },
    "verification": {
        "title": "🔐 Verificação",
        "description": "Clique no botão abaixo para se verificar e ter acesso ao servidor.",
        "button_verify": "🔓 Verificar",
        "already_verified": "✅ Você já está verificado!",
        "success": "✅ Você foi verificado com sucesso! Agora você tem acesso ao servidor."
    },
    "tickets": {
        "hub_title": "🎫 Central de Atendimento",
        "hub_description": "Selecione o tipo de atendimento que deseja:",
        "options": {
            "suporte": "🛠️ Suporte",
            "compras": "🛒 Compras",
            "denuncia": "🚨 Denúncia",
            "ajuda": "❓ Ajuda",
            "pos_venda": "📦 Pós-venda"
        },
        "welcome_title": "🎫 Ticket Aberto",
        "welcome_description": "Olá {user}!\n\nSeu ticket de **{category}** foi criado.\nUm membro da equipe responderá em breve.",
        "closed": "🔒 Ticket Fechado",
        "closed_description": "Este ticket foi fechado e será arquivado em breve.",
        "abuse": {
            "too_many_tickets": "⚠️ Você já possui o limite máximo de tickets abertos. Feche um para abrir outro.",
            "cooldown": "⚠️ Por favor, aguarde um pouco antes de criar outro ticket."
        }
    },
    "errors": {
        "not_owner": "⚠️ Apenas o proprietário do servidor pode utilizar este comando.",
        "not_admin": "⚠️ Apenas administradores podem utilizar este comando.",
        "generic": "❌ Ocorreu um erro inesperado. Tente novamente mais tarde."
    },
    "protection": {
        "spam_warning": "⚠️ Você está enviando mensagens rápido demais! Por favor, aguarde.",
        "timeout_applied": "🔇 Você foi silenciado por {duration} devido a spam.",
        "trap_ban": "🚫 Usuário banido por enviar mensagem em canal proibido."
    }
}
