import os
from tempfile import NamedTemporaryFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfWriter, PdfReader
from streamlit.runtime.uploaded_file_manager import UploadedFile
from datetime import date
from io import BytesIO
import streamlit as st
from PIL import Image
import json
import re

# Obtendo o caminho base do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminho da logo padrão
default_logo_path = os.path.join(BASE_DIR, "images", "OdontoLogo.png")

# Função para extrair informações do PDF usando expressões regulares
def extract_info_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    full_text = "".join(page.extract_text() for page in pdf_reader.pages)
    
    # Padrões regex para encontrar informações específicas
    patterns = {
        "name": r"NOME.....: \s?([\s\S]+?)\s?ENDERECO.: ",
        "cpf": r"CNPJ/CPF.:\s?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})",
        "cep": r"CEP......:\s?(\d{5}-\d{3})",
        "address": r"ENDERECO.: \s?([\s\S]+?)\s?BAIRRO...: "
    }
    
    extracted_info = {
        key: (re.search(pattern, full_text).group(1) if re.search(pattern, full_text) else "Informação não encontrada")
        for key, pattern in patterns.items()
    }
    
    # Formatando o endereço se encontrado
    if extracted_info["address"] != "Informação não encontrada":
        extracted_info["address"] = " ".join(extracted_info["address"].split())
    
    return extracted_info["name"], extracted_info["cpf"], extracted_info["cep"], extracted_info["address"]

# Função para gerar o contrato em PDF
def generate_pdf(content, logo_image=None):
    from tempfile import NamedTemporaryFile  # Import necessário para arquivos temporários
    
    # Buffer para o PDF
    pdf_buffer = BytesIO()

    # Configurações da página
    width, height = A4
    margin_x, top_margin_y, bottom_margin_y = 40, height - 50, 50
    line_spacing = 15
    max_text_width = width - 2 * margin_x

    # Criação do canvas do PDF
    c = canvas.Canvas(pdf_buffer, pagesize=A4)

    # Adicionando a logo ao PDF, se fornecida
    if logo_image:
        try:
            # Se for um UploadedFile ou BytesIO, converta para um arquivo temporário
            if isinstance(logo_image, UploadedFile) or isinstance(logo_image, BytesIO):
                logo_image.seek(0)
                with NamedTemporaryFile(delete=False, suffix=".png") as temp_logo_file:
                    temp_logo_file.write(logo_image.read())
                    temp_logo_path = temp_logo_file.name
            else:
                temp_logo_path = logo_image  # Assume que é um caminho válido

            logo_display_width, logo_display_height = 400, 126
            logo_x_position = (width - logo_display_width) / 2
            logo_y_position = height - logo_display_height - 20
            c.drawImage(temp_logo_path, logo_x_position, logo_y_position, 
                        width=logo_display_width, height=logo_display_height)
            top_margin_y = height - logo_display_height - 40

            # Removendo o arquivo temporário após uso
            if "temp_logo_path" in locals():
    # Verificar se o caminho é temporário antes de excluir
                if temp_logo_path != default_logo_path:
                    os.unlink(temp_logo_path)


        except Exception as e:
            st.error(f"Erro ao adicionar a logo: {e}")
            top_margin_y = height - 50
    else:
        top_margin_y = height - 50

    # Cabeçalho do contrato
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, top_margin_y, "Contrato")
    top_margin_y -= 30

    # Adicionando o conteúdo do contrato
    c.setFont("Helvetica", 12)
    text = c.beginText(margin_x, top_margin_y)
    text.setLeading(line_spacing)

    paragraphs = content.splitlines()
    for paragraph in paragraphs:
        if not paragraph.strip():
            text.textLine("")
        else:
            words = paragraph.split()
            line = ""
            for word in words:
                if c.stringWidth(line + " " + word, "Helvetica", 12) < max_text_width:
                    line += " " + word
                else:
                    text.textLine(line.strip())
                    line = word
            text.textLine(line.strip())
    c.drawText(text)
    c.save()

    pdf_buffer.seek(0)
    return pdf_buffer


# Função principal da página de contrato
def contrato_page():

    # Configuração da Sidebar
    st.sidebar.title("Configurações do Contrato")

    # Botão para reiniciar o fluxo
    if st.sidebar.button("Recomeçar Contrato"):
        # Limpa as variáveis do session_state para reiniciar o fluxo
        st.session_state["combined_pdf_writer"] = PdfWriter()
        st.session_state["added_contracts"] = []
        st.session_state["confirmed_data"] = None

        # Redefine outros valores importantes
        st.session_state["default_multa"] = 5.0
        st.session_state["default_juros"] = 5.0

        # Limpa o PDF carregado
        if "uploaded_pdf" in st.session_state:
            del st.session_state["uploaded_pdf"]

        # Exibe uma mensagem para indicar o reset
        st.sidebar.success("Fluxo reiniciado com sucesso! Recomece o contrato.")

    # Determinar o nome da clínica com base no username
    if "username" in st.session_state:
        if st.session_state["username"] == "abadiania":
            info_clinica = "tomas"
        elif st.session_state["username"] == "regular_user":
            info_clinica = "sorvete"
        else:
            info_clinica = "usuário desconhecido"
    else:
        info_clinica = "usuário não logado"

    # Exibir o nome da clínica de forma dinâmica
    st.sidebar.write(f"**Nome da Clínica:** {info_clinica}")

    # Upload de logo
    uploaded_logo = st.sidebar.file_uploader("Faça o upload da logo", type=["png", "jpg", "jpeg"])

    # Inicializando valores padrão no session_state para multa e juros
    if "default_multa" not in st.session_state:
        st.session_state["default_multa"] = 5.0
    if "default_juros" not in st.session_state:
        st.session_state["default_juros"] = 5.0

    # Sidebar para configurar multa e juros
    st.session_state["default_multa"] = st.sidebar.number_input(
        "Multa por atraso (%)",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        value=st.session_state["default_multa"],
        help="Insira o percentual de multa aplicado por atraso no pagamento."
    )
    st.session_state["default_juros"] = st.sidebar.number_input(
        "Taxa de juros ao mês (%)",
        min_value=0.0,
        max_value=100.0,
        step=0.1,
        value=st.session_state["default_juros"],
        help="Insira a taxa de juros mensal."
    )


    # Configuração geral
    st.title("App Geração de Contrato")

    uploaded_pdf = st.file_uploader("Faça o upload do documento PDF", type="pdf")

    # Armazenar no session_state
    if uploaded_pdf is not None:
        st.session_state["uploaded_pdf"] = uploaded_pdf

    # Inicializando session_state para contratos
    if "combined_pdf_writer" not in st.session_state:
        st.session_state["combined_pdf_writer"] = PdfWriter()

    if "added_contracts" not in st.session_state:
        st.session_state["added_contracts"] = []

    if "confirmed_data" not in st.session_state:
        st.session_state["confirmed_data"] = None

    # Extraindo e confirmando informações do PDF
    if "uploaded_pdf" in st.session_state and st.session_state["confirmed_data"] is None:
        name, cpf, cep, address = extract_info_from_pdf(st.session_state["uploaded_pdf"])
        
        st.subheader("Verifique e edite as informações, se necessário")
        name = st.text_input("Nome", name)
        cpf = st.text_input("CPF", cpf)
        cep = st.text_input("CEP", cep)
        address = st.text_input("Endereço", address)
        
        if st.button("Confirmar informações"):
            st.session_state["confirmed_data"] = {
                "name": name,
                "cpf": cpf,
                "cep": cep,
                "address": address
            }

    # Seleção de contrato e pré-visualização
    if st.session_state["confirmed_data"] is not None:
        user_data = st.session_state["confirmed_data"]
        st.write("**Informações confirmadas:**")
        st.write(f"**Nome:** {user_data['name']}")
        st.write(f"**CPF:** {user_data['cpf']}")
        st.write(f"**CEP:** {user_data['cep']}")
        st.write(f"**Endereço:** {user_data['address']}")

        st.subheader("Escolha o tipo de contrato")
        contract_option = st.selectbox("Selecione o contrato", 
                                       ["Contrato de Enxerto Ósseo", "Contrato de Implante"])
        


 #----------------------------------------------------------------------------------------------
        # Carregar usuários do arquivo JSON
        with open("users.json", "r") as file:
            users = json.load(file)

            # Verificar se o usuário está logado
        if "username" in st.session_state:
            if st.session_state["username"] in users:
                user_info = users[st.session_state["username"]]

                # Preencher as informações da clínica
                info_clinica = f"""
                Nome da Clínica (CONTRATADA): ODONTOCOMPANY\n
                Unidade: {user_info['unidade']}\n
                Endereço: {user_info['endereco']}\n
                Cirurgião Dentista Responsável: {user_info['cirurgiao_responsavel']}\n
                """
            else:
                info_clinica = "Informações da clínica não encontradas para o usuário."
        else:
            st.error("Por favor, faça login primeiro.")
            info_clinica = None

#----------------------------------------------------------------------------------------------



        contract_text = ""
        if contract_option == "Contrato de Enxerto Ósseo":


            # Input para selecionar o número do dente
            dente = st.selectbox(
                "Qual o número do dente a receber o enxerto?",
                options=[
                    11, 12, 13, 14, 15, 16, 17, 18,
                    21, 22, 23, 24, 25, 26, 27, 28,
                    31, 32, 33, 34, 35, 36, 37, 38,
                    41, 42, 43, 44, 45, 46, 47, 48
                ]
            )

            # Input para o valor total para pagamento à vista
            valor_vista = st.text_input("Informe o valor total para pagamento à vista (R$)")

            # Input para a data acordada para pagamento à vista
            data_vista = st.date_input("Data acordada para pagamento à vista", value=date.today())

            # Input para o valor do sinal
            valor_sinal = st.text_input("Valor do sinal (primeira parcela)")

            # Input para a data para pagamento do sinal
            data_sinal = st.date_input("Data para pagamento do sinal", value=date.today())

            # Input para o número total de parcelas restantes (1 a 24)
            parcelas = st.number_input(
                "Número total de parcelas restantes",
                min_value=1,
                max_value=24,
                step=1
            )

            # Input para o valor de cada parcela mensal
            valor_parcela = st.text_input("Valor de cada parcela mensal (R$)")

            # Input para o dia de vencimento das parcelas mensais (1 a 31)
            vencimento_parcelas = st.selectbox(
                "Dia de vencimento das parcelas mensais",
                options=list(range(1, 32))
            )


            multa_mora = st.session_state["default_multa"]
            juros = st.session_state["default_juros"]

            contract_text = f"""
CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO

Clínica: {info_clinica}
Nome do Manifestante (CONTRATANTE): {user_data['name']}
CPF: {user_data['cpf']}
CEP: {user_data['cep']}
Endereço: {user_data['address']}

Colocação de enxerto ósseo no(s) dente(s): {dente}.
À vista: R$ {valor_vista} (Data: {data_vista})
À prazo: R$ {valor_sinal} (Sinal: {data_sinal}), com {parcelas} parcelas de R$ {valor_parcela}, vencendo no dia {vencimento_parcelas}.
Multa por atraso: {multa_mora}%.
Juros mensais: {juros}%.
"""
        if contract_text:
            st.subheader("Pré-visualização do Contrato")
            st.text_area("Contrato", contract_text, height=200)

            if st.button("Adicionar Contrato"):
                # Use a logo enviada pelo usuário ou a logo padrão
                logo_to_use = uploaded_logo if uploaded_logo else default_logo_path
                pdf_data = generate_pdf(contract_text, logo_image=logo_to_use)
                st.session_state["combined_pdf_writer"].add_page(PdfReader(pdf_data).pages[0])
                st.session_state["added_contracts"].append(contract_text)
                st.success("Contrato adicionado com sucesso!")

            if st.session_state["added_contracts"]:
                st.subheader("Contratos Adicionados")
                for idx, contract in enumerate(st.session_state["added_contracts"], start=1):
                    st.text_area(f"Contrato {idx}", contract, height=200)

            if st.button("Finalizar e Baixar"):
                combined_pdf = BytesIO()
                st.session_state["combined_pdf_writer"].write(combined_pdf)
                combined_pdf.seek(0)
                st.download_button(
                    label="Baixar Contratos Combinados",
                    data=combined_pdf.getvalue(),
                    file_name="contratos_combinados.pdf",
                    mime="application/pdf"
                )
                st.session_state["combined_pdf_writer"] = PdfWriter()
                st.session_state["added_contracts"] = []

#cd C:\Users\tomas\OneDrive\Área de Trabalho\ContratoPDF && ambienteVirtual\Scripts\activate && streamlit run login.py
