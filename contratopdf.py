import streamlit as st
import re
from PyPDF2 import PdfReader
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def extract_info_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    full_text = ""
    
    # Extrai o texto de todas as páginas do PDF
    for page in pdf_reader.pages:
        full_text += page.extract_text()
    
    # Ajuste dos padrões de busca para Nome, CPF, RG, CEP e Endereço
    name_pattern = r"NOME.....: \s?([\s\S]+?)\s?ENDERECO.: "
    cpf_pattern = r"CNPJ/CPF.:\s?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})"  # Captura com ou sem pontuação
    cep_pattern = r"CEP......:\s?(\d{5}-\d{3})"
    address_pattern = r"ENDERECO.: \s?([\s\S]+?)\s?BAIRRO...: "  # Captura texto entre "Endereço:" e "Gênero:"

    # Ajuste dos padrões de busca para Nome, CPF, RG, CEP e Endereço ORIGINAL
    #name_pattern = r"Nome:\s?([A-Z\s]+)"
    #cpf_pattern = r"CPF:\s?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})"  # Captura com ou sem pontuação
    #rg_pattern = r"RG:\s?(\d+)"
    #cep_pattern = r"CEP:\s?(\d{5}-\d{3})"
    #address_pattern = r"Endereço:\s?([\s\S]+?)\s?Gênero:"  # Captura texto entre "Endereço:" e "Gênero:"
    
    # Realiza as buscas no texto usando os padrões definidos
    name_match = re.search(name_pattern, full_text)
    cpf_match = re.search(cpf_pattern, full_text)
    cep_match = re.search(cep_pattern, full_text)
    address_match = re.search(address_pattern, full_text)
    
    # Extrai as informações encontradas ou exibe mensagem caso não encontre
    name = name_match.group(1) if name_match else "Nome não encontrado no documento."
    cpf = cpf_match.group(1) if cpf_match else "CPF não encontrado no documento."
    cep = cep_match.group(1) if cep_match else "CEP não encontrado no documento."
    
    # Processa o endereço para substituir múltiplos espaços ou quebras de linha por um único espaço
    if address_match:
        address = " ".join(address_match.group(1).split())
    else:
        address = "Endereço não encontrado no documento."
    
    return name, cpf, cep, address  # Retorna todas as informações extraídas



# O restante do código permanece o mesmo
def generate_pdf(content):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    
    # Define margens e limites de largura para o texto
    width, height = A4
    margin_x = 50  # Margem horizontal
    margin_y = 750  # Posição inicial vertical
    max_text_width = width - 2 * margin_x  # Largura máxima do texto
    line_spacing = 15  # Espaçamento entre linhas

    # Título do PDF
    c.setFont("Helvetica-Bold", 14)  # Define a fonte e o tamanho para o título
    c.drawString(margin_x, margin_y, "Contrato")  # Desenha o título
    margin_y -= 30  # Reduz a posição vertical após o título
    
    # Adiciona o conteúdo linha por linha
    c.setFont("Helvetica", 12)  # Define a fonte e o tamanho para o conteúdo
    text = c.beginText(margin_x, margin_y)  # Define a origem do texto no PDF
    text.setLeading(line_spacing)  # Define o espaçamento entre linhas
    words = content.split()  # Divide o conteúdo em palavras
    line = ""  # Variável para montar cada linha de texto

    # Monta as linhas, testando se cada linha cabe no limite de largura
    for word in words:
        # Verifica se a linha mais a próxima palavra excede a largura máxima
        if c.stringWidth(line + " " + word, "Helvetica", 12) < max_text_width:
            line += " " + word  # Adiciona a palavra à linha se couber
        else:
            text.textLine(line.strip())  # Desenha a linha atual no PDF
            line = word  # Inicia uma nova linha com a palavra que não coube
    text.textLine(line.strip())  # Adiciona a última linha de texto ao PDF

    c.drawText(text)  # Adiciona o texto ao PDF
    c.showPage()  # Finaliza a página
    c.save()  # Salva o PDF no buffer
    pdf_buffer.seek(0)  # Reseta o buffer para o início
    return pdf_buffer  # Retorna o PDF como um objeto de bytes

st.title("App Geração de Contrato")

# Carrega o arquivo PDF
uploaded_pdf = st.file_uploader("Faça o upload do documento PDF", type="pdf")

# Inicializa o estado para armazenar dados confirmados
if "confirmed_data" not in st.session_state:
    st.session_state["confirmed_data"] = None

# Verifica se o PDF foi carregado e se não há dados confirmados
if uploaded_pdf is not None and st.session_state["confirmed_data"] is None:
    # Extrai informações do PDF carregado
    name, cpf, cep, address = extract_info_from_pdf(uploaded_pdf)
    
    # Exibe as informações para o usuário verificar e permitir edições
    st.subheader("Verifique e edite as informações, se necessário")
    name = st.text_input("Nome", name)
    cpf = st.text_input("CPF", cpf)
    cep = st.text_input("CEP", cep)
    address = st.text_input("Endereço", address)
    
    # Confirma as informações e salva no estado da sessão
    if st.button("Confirmar informações"):
        st.session_state["confirmed_data"] = {
            "name": name,
            "cpf": cpf,
            "cep": cep,
            "address": address
        }

# Verifica se as informações foram confirmadas
if st.session_state["confirmed_data"] is not None:
    user_data = st.session_state["confirmed_data"]  # Recupera os dados confirmados
    st.write("**Informações confirmadas:**")
    st.write(f"**Nome:** {user_data['name']}")
    st.write(f"**CPF:** {user_data['cpf']}")
    st.write(f"**CEP:** {user_data['cep']}")
    st.write(f"**Endereço:** {user_data['address']}")
    
    # Exibe a opção de selecionar o tipo de contrato
    st.subheader("Escolha o tipo de contrato")
    contract_option = st.selectbox("Selecione o contrato", ["Contrato Aceito Sorvete", "Contrato Não Quero Sorvete"])
    
    # Define o texto do contrato com base na seleção do usuário
    if contract_option == "Contrato Aceito Sorvete":
        contract_text = f"""
        Eu, {user_data['name']}, e CPF {user_data['cpf']}, residente no endereço {user_data['address']}, CEP {user_data['cep']},
        declaro que aceito Sorvete.
        """
    else:
        contract_text = f"""
        Eu, {user_data['name']}, e CPF {user_data['cpf']}, residente no endereço {user_data['address']}, CEP {user_data['cep']},
        declaro que não quero sorvete.
        """
    
    # Exibe a pré-visualização do contrato na interface
    st.subheader("Pré-visualização do Contrato")
    st.text_area("Contrato", contract_text, height=200)
    
    # Gera o PDF do contrato e exibe o botão de download
    pdf_data = generate_pdf(contract_text)
    st.download_button(
        label="Baixar contrato em PDF",
        data=pdf_data,
        file_name="contrato.pdf",
        mime="application/pdf"
    )
else:
    st.write("Por favor, carregue um documento PDF para extrair as informações.")


# cd C:\Users\tomas\OneDrive\Área de Trabalho\ContratoPDF
# ambienteVirtual\Scripts\activate
# streamlit run pages/corrigido.py

# cd C:\Users\tomas\OneDrive\Área de Trabalho\ContratoPDF && ambienteVirtual\Scripts\activate && streamlit run contratopdf.py
