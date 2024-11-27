import streamlit as st

# Título da página
st.title("Dúvidas Frequentes")

# Perguntas e respostas de exemplo
faq = [
    {
        "question": "Como faço o upload de um PDF?",
        "answer": "Você pode carregar um arquivo PDF clicando no botão 'Faça o upload do documento PDF' na página principal. Certifique-se de que o arquivo está no formato correto."
    },
    {
        "question": "Posso adicionar uma logo personalizada?",
        "answer": "Sim, você pode adicionar uma logo personalizada na sidebar, escolhendo a opção 'Adicionar outra logo'. Caso contrário, a logo padrão será usada."
    },
    {
        "question": "Como adicionar mais contratos?",
        "answer": "Depois de preencher as informações do contrato, clique no botão 'Adicionar Contrato'. O contrato será salvo na lista e exibido na seção 'Contratos Adicionados'."
    },
    {
        "question": "Como faço para baixar todos os contratos adicionados?",
        "answer": "Após adicionar todos os contratos desejados, clique no botão 'Finalizar e Baixar'. Isso gerará um arquivo PDF com todos os contratos adicionados."
    },
    {
        "question": "O que acontece com os contratos depois que eu finalizo o download?",
        "answer": "Os contratos são removidos do sistema após o download para garantir sua privacidade e segurança."
    },
    {
        "question": "Posso editar um contrato após adicioná-lo?",
        "answer": "Não. Para editar um contrato, você precisará recomeçar o processo de adição do mesmo."
    }
]

# Exibir as perguntas e respostas na página
st.write("Aqui estão algumas perguntas e respostas comuns para ajudá-lo:")
for item in faq:
    st.subheader(item["question"])
    st.write(item["answer"])
