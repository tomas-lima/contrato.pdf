from tempfile import NamedTemporaryFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PyPDF2 import PdfReader
from io import BytesIO
import streamlit as st
from PIL import Image
import os
import re

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
    
    # Extraindo informações de acordo com os padrões
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
    # Buffer para o PDF
    pdf_buffer = BytesIO()

    # Configurações da página
    width, height = A4
    margin_x, top_margin_y, bottom_margin_y = 40, height - 50, 50
    line_spacing = 15
    max_text_width = width - 2 * margin_x
    available_height = top_margin_y - bottom_margin_y
    lines_per_page = int(available_height / line_spacing)

    # Função para contar o número de páginas
    def count_pages():
        line_count = 0
        page_count = 1
        for paragraph in paragraphs:
            if not paragraph.strip():
                line_count += 1
            else:
                words = paragraph.split()
                line = ""
                for word in words:
                    if canvas.Canvas(pdf_buffer).stringWidth(line + " " + word, "Helvetica", 12) < max_text_width:
                        line += " " + word
                    else:
                        line_count += 1
                        line = word
                    if line_count >= lines_per_page:
                        page_count += 1
                        line_count = 0
                line_count += 1
            if line_count >= lines_per_page:
                page_count += 1
                line_count = 0
        return page_count

    # Quebrando o conteúdo em parágrafos
    paragraphs = content.splitlines()
    total_pages = count_pages()

    # Criação do canvas do PDF
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    page_number = 1

    # Adicionando a logo ao PDF, se fornecida
    if logo_image:
        logo_image = Image.open(logo_image)
        with NamedTemporaryFile(delete=False, suffix=".png") as temp_logo_file:
            logo_image.save(temp_logo_file, format="PNG")
            temp_logo_path = temp_logo_file.name

        # Definindo dimensões fixas de exibição
        logo_display_width, logo_display_height = 400, 126 # inicial era 400 x 126
        logo_x_position = (width - logo_display_width) / 2  # Centraliza a imagem horizontalmente
        logo_y_position = height - logo_display_height - 20  # Define a posição vertical
        c.drawImage(temp_logo_path, logo_x_position, logo_y_position, width=logo_display_width, height=logo_display_height)

        os.remove(temp_logo_path)
        top_margin_y -= logo_display_height + 20

    # Cabeçalho do contrato
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, top_margin_y, "Contrato")
    top_margin_y -= 30

    # Adicionando o conteúdo do contrato
    c.setFont("Helvetica", 12)
    text = c.beginText(margin_x, top_margin_y)
    text.setLeading(line_spacing)
    line_count = 0

    for paragraph in paragraphs:
        if not paragraph.strip():
            line_count += 1
            if line_count >= lines_per_page:
                c.drawText(text)
                c.setFont("Helvetica", 8)
                c.drawRightString(width - margin_x, bottom_margin_y, f"Página {page_number} de {total_pages}")
                c.showPage()
                page_number += 1
                text = c.beginText(margin_x, height - 50)
                line_count = 0
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
                    line_count += 1
                    if line_count >= lines_per_page:
                        c.drawText(text)
                        c.setFont("Helvetica", 8)
                        c.drawRightString(width - margin_x, bottom_margin_y, f"Página {page_number} de {total_pages}")
                        c.showPage()
                        page_number += 1
                        text = c.beginText(margin_x, height - 50)
                        line_count = 0
            text.textLine(line.strip())
            line_count += 1

    # Finalizando o PDF
    c.drawText(text)
    c.setFont("Helvetica", 8)
    c.drawRightString(width - margin_x, bottom_margin_y, f"Página {page_number} de {total_pages}")
    c.showPage()
    c.save()
    
    # Retorna o buffer do PDF
    pdf_buffer.seek(0)
    return pdf_buffer

# Interface do aplicativo Streamlit
st.title("App Geração de Contrato")
uploaded_pdf = st.file_uploader("Faça o upload do documento PDF", type="pdf")

# Armazenando as informações confirmadas
if "confirmed_data" not in st.session_state:
    st.session_state["confirmed_data"] = None

# Extraindo e confirmando informações do PDF
if uploaded_pdf is not None and st.session_state["confirmed_data"] is None:
    name, cpf, cep, address = extract_info_from_pdf(uploaded_pdf)
    
    st.subheader("Verifique e edite as informações, se necessário")
    name = st.text_input("Nome", name)
    cpf = st.text_input("CPF", cpf)
    cep = st.text_input("CEP", cep)
    address = st.text_input("Endereço", address)
    
    # Opção para carregar a logo nesta etapa
    uploaded_logo = st.file_uploader("Faça o upload da logo, caso não faça será utilizada a logo padrão Odonto Company", type=["png", "jpg", "jpeg"])
    logo_image = uploaded_logo if uploaded_logo else 'images/OdontoLogo.png'
    
    if st.button("Confirmar informações"):
        st.session_state["confirmed_data"] = {
            "name": name,
            "cpf": cpf,
            "cep": cep,
            "address": address,
            "logo": logo_image
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
                                   [
                                    "Contrato de Enxerto Ósseo", 
                                    "Contrado de Implante",
                                    "Contrato Orto",
                                    "Contrato Plano ODC Novo",
                                    "Contrato Preenchimento",
                                    "Contrato Procedimentos Gerais",
                                    "Contrato Prótese",
                                    "Contrato Implantes",
                                    "Contrato Botox",
                                    "Contrato Canal"
                                    ])
    
    # insere as informações da clínica, futuramente será dinâmico com o usuário
    info_clinica = f""" 
     Nome da Clínica (CONTRATADA): ODONTOCOMPANY\n
     Unidade: Abadia de Goiás\n
     Endereço: Av. Comercial, Qd 6 Lt 5, Centro, 75345-959\n 
     Cirurgião Dentista Responsável: Mariana Silva Xavier, CRO/GO 17928\n 
     \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n

     """
    
    # Definindo a variável de assinaturas
    assinaturas = f""" 
     DATA: ____________/______________/_____________\n\n

    ENDEREÇO:______________________________________________________________________\n\n\n

    Paciente (CONTRATANTE): _____________________________\n\n
    
    Testemunha 1: _______________________________________\n\n\n

    CLÍNICA (CONTRATADO): _______________________________\n\n

    Testemunha 2: _______________________________________\n\n

     """
    
    

    contract_text = ""  # Inicializando o contrato
    

    # *************************************************************************************

    #                   INICIO DOS CONTRATOS

    # *************************************************************************************


    # *************************************************************************************

    #                   CONTRATO ENXERTO OSSEO

    # *************************************************************************************


    if contract_option == "Contrato de Enxerto Ósseo":
        dente = st.text_input("Qual o número do dente a receber o enxerto?")
        valor_vista = st.text_input("Informe o valor total para pagamento à vista (R$)")
        data_vista = st.text_input("Data acordada para pagamento à vista")
        valor_sinal = st.text_input("Valor do sinal (primeira parcela)")
        data_sinal = st.text_input("Data para pagamento do sinal")
        parcelas = st.text_input("Número total de parcelas restantes")
        valor_parcela = st.text_input("Valor de cada parcela mensal (R$)")
        vencimento_parcelas = st.text_input("Dia de vencimento das parcelas mensais")
        multa_mora = st.text_input("Multa aplicada por atraso no pagamento (%)")
        juros = st.text_input("Taxa de juros aplicada ao mês (%)")
        contract_text = f"""

        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:\n\n
I – Fase de Orientação:\n

O paciente será, nesta fase, orientado a respeito do que são enxertos, das suas diversas técnicas, do tratamento, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente.\n
Nesta fase o paciente tomará ciência de que a integração e cicatrização do enxerto é dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente, não havendo outra garantia da sua ocorrência, além da probabilidade estatística.\n
Parágrafo único – O paciente ficará esclarecido e ciente de que a natureza deste tratamento objetiva a recuperação óssea e que estética não será o objetivo do mesmo.\n\n
II – Fase de Planejamento:\n

Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.\n
Parágrafo único: Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento.\n\n
III – Fase cirúrgica:\n

Colocação de enxerto ósseo assim distribuídos na região do(s) dente(s) _____________{dente}________________________.\n\n
IV – Fase de preservação:\n

A fase de preservação terá a seguinte duração:\n

No primeiro mês: uma consulta semanal ou mensal, dependendo do caso.\n

Nos 3 (três) meses seguintes: uma consulta mensal.\n

Parágrafo 1º - Na fase de preservação o paciente será orientado sobre a escovação e higiene e dos cuidados que deverá tomar para a preservação do enxerto.\n
Parágrafo 2º - A fase de preservação é obrigatória, sendo que, a falta do paciente às consultas marcadas prejudicará definitivamente o prognóstico do enxerto.\n
Parágrafo 3º - Em caso de não ocorrer a cicatrização e integração o cirurgião compromete-se a recolocar outro enxerto, quando as condições do tecido ósseo permitirem, cabendo ao paciente apenas o pagamento do novo enxerto e do material.\n
O paciente está ciente de que a cicatrização e integração do enxerto é um fenômeno dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente.\n
Parágrafo 4º - O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento e a permanecer sem o uso da prótese se necessário.\n
Parágrafo 5º - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião, ou por sua ausência as consultas marcadas, o cirurgião ficará isento de responsabilidade sobre o enxerto ósseo colocado.\n
Nestes casos, a recolocação do enxerto ficará a critério do cirurgião dentista.\n
Parágrafo 6º - O paciente fica consciente de que, em alguns casos, não será possível a recolocação do enxerto ósseo sendo neste caso proposto outro tipo de tratamento.\n\n
V – Do pagamento:\n

A remuneração pecuniária do tratamento ora proposto, será da seguinte maneira:\n
À vista: R$ {valor_vista} data {data_vista}\n
À prazo/sinal: R$ {valor_sinal} data {data_sinal} e o restante em {parcelas} parcelas no valor de {valor_parcela} com vencimento nos dias {vencimento_parcelas}.\n
Parágrafo 1º - O paciente concorda que os pagamentos vencidos e efetuados fora dos prazos previstos anteriormente estarão sujeitos a multa de mora {multa_mora}% e juros de {juros}% ao mês.\n
Parágrafo 2º - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o (a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.\n\n
VI – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10% a qual o paciente está ciente e de acordo com a mesma.\n
Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.\n\n
VII – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n\n
VIII – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n\n
VIII - Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.\n
Parágrafo 1° – Fica acordado que o CONTRATANTE poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
Parágrafo 2° – O CONTRATANTE irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter inicio.\n
Parágrafo 3° – Em caso de mais de 1 (um) procedimento, caberá ao CONTRATADO realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do CONTRATANTE.\n\n
IX – A responsabilidade do cirurgião dentista baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.\n\n
X – O paciente, neste ato, doa todo o material de diagnóstico e planejamento (radiografias, modelos, slides, exames complementares) trazido pelo mesmo ou obtido durante o tratamento o qual passa a ser propriedade e documento do cirurgião dentista, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica serão arquivados com o cirurgião dentista.\n
O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.\n
As partes elegem o Fórum da Comarca de Anápolis/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, ainda que mais favorável for.\n\n

{assinaturas}

            """



    # *************************************************************************************

    #                   CONTRATO IMPLANTES

    # *************************************************************************************


    elif contract_option == "Contrato de Implante":
        enxerto = st.text_input("Existe necessidade de enxerto ósseo? (Sim/Não)")
        valor_vista = st.text_input("Informe o valor total para pagamento à vista (R$)")
        data_vista = st.text_input("Data combinada para pagamento à vista")
        valor_sinal = st.text_input("Valor da entrada (sinal)")
        data_sinal = st.text_input("Data para pagamento do sinal")
        parcelas = st.text_input("Quantidade de parcelas restantes")
        valor_parcela = st.text_input("Valor de cada parcela mensal (R$)")
        vencimento_parcelas = st.text_input("Dia de vencimento das parcelas mensais")
        multa_mora = st.text_input("Multa por atraso (%)")
        juros = st.text_input("Taxa de juros ao mês (%)")
        resto_pagamento = st.text_input("Detalhe a forma de divisão dos valores restantes para pagamento")


        contract_text = f"""


        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:\n\n

I – Fase de Orientação: O paciente será, nesta fase, orientado a respeito do que são implantes ósseo-integrados e os diversos tipos de enxertos ósseos que podem se fazer necessários em algum momento do tratamento, das suas diversas técnicas, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente.\n
Nesta fase o paciente tomará ciência de que a ósseo-integração é dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente, não havendo outra garantia da sua ocorrência, além da probabilidade estatística.\n
Parágrafo único – O paciente ficará esclarecido e ciente de que existem fatores clínicos e que são necessários exames de imagem de última geração, mas que a odontologia é uma ciência inexata, e que podem se fazer necessários outros tipos de intervenções no tratamento, que em caso de necessidade serão negociadas à parte.\n\n

II – Fase de Planejamento: Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.\n
Parágrafo único: Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento.\n\n

III – Fase cirúrgica: PROTOCOLO INFERIOR DE PORCELANA E IMPLANTE DENTE N°12\n
Necessidade de enxerto?_______________ {enxerto} ______________________.\n\n

IV – Fase protética: esta fase será assim dividida:\n
Prótese cirúrgica: a critério do cirurgião dentista e baseado nas características de cada caso, poderá ser confeccionada uma prótese provisória, aqui considerada cirúrgica, que tem a finalidade de proteção dos implantes, não devolvendo ao paciente estética ou função.\n
Parágrafo único: a critério do cirurgião a prótese cirúrgica poderá ser a própria do paciente devidamente adaptada, se em perfeita condição para o caso.\n\n

V – Fase de preservação: A fase de preservação se inicia após a terceira consulta pós-operatória, e terá a duração 4 (quatro) ou 6 (meses), podendo ocorrer consultas mensalmente, quando necessário, e em seguida, será marcada a cirurgia de exposição dos implantes onde será constatada ou não a ósseo-integração dos mesmos.\n
Parágrafo 1º - Na fase de preservação o paciente será orientado sobre a escovação e higiene dos implantes e dos cuidados que deverá tomar para sua preservação.\n
Parágrafo 2º - A fase de preservação é obrigatória, sendo que, a falta do paciente às consultas marcadas prejudicará definitivamente o prognóstico dos implantes.\n
Parágrafo 3º - Em caso de não ocorrer a ósseo-integração o cirurgião compromete-se a recolocar outro implante, quando as condições do tecido ósseo permitirem, cabendo ao paciente apenas o pagamento do novo implante e do material. O paciente está ciente de que a ósseo-integração é um fenômeno dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente.\n
Parágrafo 4º - O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento e a permanecer sem o uso da prótese se necessário.\n
Parágrafo 5º - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião, ou por sua ausência as consultas marcadas, o cirurgião ficará isento de responsabilidade sobre os implantes colocados. Nestes casos, a recolocação do implante ficará a critério do cirurgião dentista.\n
Parágrafo 6º - O paciente fica consciente de que, em alguns casos, não será possível a recolocação de implantes sendo neste caso proposto outro tipo de tratamento.\n\n

VI – Do pagamento: a remuneração pecuniária do tratamento ora proposto, será da seguinte maneira:\n
À vista: R$ {valor_vista} data {data_vista}\n
À prazo/sinal: R$ {valor_sinal} data {data_sinal} e o restante em {parcelas} parcelas no valor de {valor_parcela} com vencimento nos dias {vencimento_parcelas}. Peculiaridades em relação ao meio de pagamento: {resto_pagamento} \n
Parágrafo 1º - O paciente concorda que os pagamentos vencidos e efetuados fora dos prazos previstos anteriormente estarão sujeitos a multa de mora {multa_mora} % e juros de {juros} % ao mês.\n
Parágrafo 2º - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o (a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.\n\n

VII – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10% a qual o paciente está ciente e de acordo com a mesma. Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.\n\n

VIII – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n\n

IX – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n\n

X – Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.\n
Parágrafo 1° – Fica acordado que o CONTRATANTE poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
Parágrafo 2° – O CONTRATANTE irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter início.\n
Parágrafo 3° – Em caso de mais de 1 (um) procedimento, caberá ao CONTRATADO realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do CONTRATANTE.\n\n

X – A responsabilidade do cirurgião dentista baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.\n\n

XI – O paciente, neste ato, doa todo o material de diagnóstico trazido pelo mesmo ou obtido durante o tratamento o qual passa a ser propriedade do cirurgião dentista, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica serão arquivados com o cirurgião dentista.\n\n

O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.\n\n

As partes elegem o Fórum da Comarca de Anápolis/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, por mais privilegiado for.\n\n

{assinaturas}


        """

    # *************************************************************************************

    #                   CONTRATO ORTO ONEROSA

    # *************************************************************************************


    elif contract_option == "Contrato Orto":
        alergia = st.text_input("Possui alergia a algum medicamento? Se sim, qual?")
        medicamentos = st.text_input("Utiliza algum medicamento? Indique quais.")
        qdt_cigarros = st.text_input("Número de cigarros consumidos diariamente (se for fumante)")
        doencas = st.text_input("Já teve ou possui alguma das seguintes doenças:")
        info_necessarias = st.text_input("Outras informações relevantes para o tratamento:")
        diagnostico = st.text_input("Diagnóstico do tratamento")
        prognostico = st.text_input("Prognóstico previsto")
        desc_aparelhos = st.text_input("Descrição dos aparelhos ortodônticos a serem usados")
        estima_tratamento = st.text_input("Duração estimada do tratamento (em meses)")
        brackts = st.text_input("Valor dos brackets por peça (em caso de reposição)")
        mensalidade = st.text_input("Valor da mensalidade do tratamento")


        contract_text = f"""


        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:\n
1-Esclarecimentos Gerais:\n
Por favor, leia com atenção este documento e esclareça todas as suas dúvidas antes de assiná-lo. A intenção de seu dentista não é assustá-lo(a), nem deixá-lo(a) desconfortável com o procedimento que vai se submeter, mas informá-lo(a) sobre seus benefícios esperados, riscos, desconfortos, e isso, porque você tem o direito de saber. Nenhum ato será praticado sem que você concorde.\n
O paciente tem ciência de que a odontologia depende de fatores biológicos pertinentes a cada paciente, e não sendo uma ciência exata, não lhe é assegurada nenhuma garantia de sucesso, e que depende muito de um paciente cooperativo.\n
Um plano de tratamento será fornecido, porém está sujeito a alterações, uma vez que a resposta do organismo e padrão de crescimento são observados. Essas mudanças podem envolver extrações de dentes permanentes, cirurgia ortognática, etc. Esses procedimentos deverão ser realizados pela clínica/cirurgião dentista de sua escolha sob solicitação por escrito.\n\n
Declaro que:\n
Já tive reação alérgica a: {alergia}..........................................................\n
Faço uso dos seguintes medicamentos: {medicamentos}............................\n
Sou fumante, fazendo uso de {qdt_cigarros}.............. cigarros diariamente;\n
Já tive ou ainda sou portador(a) das seguintes doenças: {doencas}...............\n
Demais informações que julgar necessárias:{info_necessarias}........................\n
Tenho conhecimento de que qualquer omissão da minha parte poderá me trazer prejuízos, comprometer o procedimento a que me submeto, causar-me sequelas ou acarretar danos à minha saúde.\n\n
2- Planejamento:\n
O profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.\n
Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento.\n\n
3-Atendimento:\n
Antecipadamente o paciente ou representante legal autoriza a clínica sob supervisão do cirurgião dentista a realizar seu tratamento ortodôntico, tendo em vista que este foi elaborado na avaliação do questionário de anamnese geral e odontológico, dos exames clínicos e radiográficos, e se necessário, complementado com exames laboratoriais, fotografias e modelos da arcada dentária.\n
O paciente será sempre atendido uma vez ao mês, podendo não ser atendido de acordo com o plano de tratamento. Quando houver algum problema com o aparelho ou dúvidas, o paciente poderá alterar o horário de sua consulta comunicando de preferência com 24 horas de antecedência.\n
O paciente que não comparecer à consulta ficará responsável por telefonar para remarcar nova consulta e receberá o atendimento o mais breve possível.\n
O paciente ou representante legal deverá comunicar a clínica por escrito, toda e qualquer alteração que ocorra em seu endereço, inclusive telefone.\n
O paciente que não comparecer à consulta mensal do tratamento, fica obrigado a pagar a mensalidade estabelecida neste instrumento independentemente do seu comparecimento.\n\n
4-Interrupção do tratamento:\n
O paciente ou responsável pode a qualquer momento desistir do tratamento, devendo avisar com antecedência, bastando para tanto que comunique sua decisão ao seu dentista(a) e assine o Termo de Revogação, abaixo transcrito. Se a desistência ocorrer, será cobrada uma multa contratual no valor de 10% (dez por cento) do valor do contrato, ressalvado ainda o direito do recebimento proporcional dos serviços realizados, que será apresentado pela clínica.\n
O aparelho deverá ser removido imediatamente.\n
O paciente que não apresentar assiduidade às consultas, não mantiver uma higiene bucal correta, provocar quebras constantes em seu aparelho, terá seu tratamento replanejado junto ao responsável para uma continuidade ou não do mesmo.\n
O paciente que se ausentar por 6 (seis) meses e não comunicar por escrito o motivo se responsabiliza por qualquer problema que venha ocorrer em decorrência da falta de manutenção. Automaticamente isentando o cirurgião dentista de qualquer responsabilidade por problemas que venham a ocorrer.\n\n
5-Final de tratamento ou desistência:\n
Em casos de término ou desistência do tratamento, o paciente não deverá em hipótese alguma continuar fazendo uso de qualquer aparatologia ortodôntica ou ortopédica instalado pela clínica, visto que estará sem o acompanhamento do cirurgião dentista que o planejou e instalou. Isso pode provocar danos irreparáveis ao paciente.\n\n
6-Contenção:\n
A contenção é utilizada normalmente após a finalização de cada etapa do tratamento, a fim de manter os dentes em suas novas posições até que se complete a formação de novo tecido ósseo em torno dos mesmos, e até que lábios e língua tenham se adaptado a essas posições. Sem o uso apropriado da contenção, os dentes tenderão a se mover para suas posições originais.\n
Após a colocação do aparelho de contenção, o paciente se obriga a retornar ao consultório no mínimo ...... (...........) vezes, sendo o intervalo entre as consultas pré-determinado pelo cirurgião dentista.\n\n
7-Informações específicas sobre o tratamento ortodôntico a ser realizado:\n
Diagnóstico: {diagnostico}...........................................................................\n
Prognóstico: {prognostico}..............................................................................\n
Descrição geral dos aparelhos a serem utilizados:{desc_aparelhos}...............\n
Previsão estimada do tempo de tratamento:{estima_tratamento}....................\n
Declaro que li e fui esclarecido pelo(a) dentista e entendi adequadamente todos os procedimentos que serão realizados durante o tratamento, inclusive as reações e consequências que podem surgir durante e após a aplicação do tratamento.\n
Tive a oportunidade de esclarecer todas as minhas dúvidas sobre o procedimento a que vou me submeter, sobre os cuidados no durante e no pós-tratamento a qual tenho o dever de cumprir, tendo lido e compreendido todas as informações deste documento, antes da sua assinatura.\n
Declaro também que seguirei todas as orientações sobre todos os cuidados a serem realizados a fim de não comprometer os resultados de meu Tratamento dentário.\n\n
8-Valores e formas de pagamento:\n
O pagamento do tratamento ortodôntico será feito através de mensalidades no valor previamente informado enquanto durar o tratamento, que neste contrato será inicialmente no valor de R$..........{mensalidade}........................\n
As mensalidades deverão ser pagas independentemente da frequência do paciente no consultório. A primeira mensalidade deverá ser paga no início do tratamento.\n
Independentemente da data de assinatura do contrato, o reajuste das mensalidades poderá ser efetuado todo dia 1º (primeiro) de janeiro de cada ano.\n
Na hipótese de pagamento com atraso de qualquer parcela, o paciente se obriga a solvê-la pelo valor vigente no dia do pagamento acrescido de multa de 2% (dois por cento) ao mês sobre o valor total, além de juros moratórios de 1%( um por cento) ao mês, de acordo com índice oficial.\n
Em casos de mensalidades atrasadas, o paciente não poderá continuar o tratamento até quitação das mesmas, se responsabilizando pelas consequências da falta de manutenção.\n
Caso ocorra quebra, perda e/ou falta de cuidado com o aparelho, as peças quebradas serão cobradas à parte do paciente, em especial os denominados ‘’brackts’’ no valor de R$ ......{brackts}........... por peça, e o paciente, através da assinatura do presente instrumento, declara ciência e concordância de tal pagamento.\n
Cirurgias e outros tratamentos clínicos não estão incluídos no tratamento aqui proposto.\n\n
9 – Da rescisão:\n
Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, além do recebimento proporcional dos serviços realizados até a data da desistência, além de uma multa rescisória de 10% (dez por cento) a qual o paciente está ciente e de acordo com a mesma.\n
Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.\n
Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n
Fica acordado entre as partes que a realização de quaisquer outros tratamentos irá ficar condicionada à realização de novo contrato, sendo que o condicionamento de início destes outros tratamentos/procedimentos será o pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n
Fica acordado em casos destes outros tratamentos/procedimentos que:\n
Fica acordado que o CONTRATANTE poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
O CONTRATANTE irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter início.\n
Em caso de mais de 1 (um) procedimento, caberá ao CONTRATADO realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do CONTRATANTE.\n\n
10-Do Foro:\n
As partes elegem o foro da comarca de Anápolis/GO, para eliminar quaisquer dúvidas oriundas deste documento, renunciando, desde já, qualquer outro por mais privilegiado que o seja.\n\n
E por estarem justos e de comum acordo, assinam o presente documento na presença de duas testemunhas, abaixo identificadas, em 2 (duas) vias de igual forma e teor.

{assinaturas}

ATENÇÃO:
As informações prestadas neste termo não esgotam todas as possibilidades de riscos e complicações que possam advir do procedimento, apenas são enumeradas algumas.
A intenção do seu dentista não é assustá-lo nem deixá-lo desconfortável com o procedimento que você vai se submeter, mas cumprir com o dever de informação, esclarecendo que qualquer procedimento na área da saúde implica em riscos, ainda que ocorram apenas excepcionalmente.
Sempre poderá o paciente ou representante legal pedir informações e discutir com o seu dentista todas as suas dúvidas. Nenhum ato será praticado sem que você concorde.
Portanto, necessário o entendimento de todas as informações recebidas. Em caso de dúvidas, antes de assinar esse documento, deverá haver perguntas para total esclarecimento e pergunte o que quiser antes de assinar este documento, pois esta é a autorização para que o procedimento seja realizado.


        """

    # *************************************************************************************

    #                   CONTRATO PLANO ODC NOVO

    # *************************************************************************************


    elif contract_option == "Contrato Plano ODC Novo":
        entrada = st.text_input("Valor da entrada (R$)")
        restante = st.text_input("Forma de pagamento do valor restante")
        carne = st.text_input("Valor total do carnê (R$)")

        
        contract_text = f"""


        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

As partes acima qualificadas e ora contratadas, resolvem na melhor forma de direito firmar o presente Contrato de Compra e Venda de Serviços Odontológicos de acordo com os termos abaixo elencados:\n\n
De início, para fins de esclarecimento, fica expresso que o presente Contrato de Compra e Venda de Serviços Odontológicos não é Plano de Saúde/Odontológico e nem um Seguro Saúde/Odontológico. Declara a VENDEDORA, neste ato, que não possui vínculo com a assistência da saúde e não está vinculada à ANS – Agência Nacional de Saúde Suplementar.\n
Assim, o presente contrato se trata de uma forma de compra pré-paga e/ou pós-paga de serviços odontológicos, que assegura ao(s) COMPRADOR(ES) apenas os serviços, preços e descontos aqui expressos.\n\n
Cláusula 1 - A VENDEDORA se obriga a prestar serviços odontológicos ao(s) COMPRADOR(ES), proporcionando atendimento de natureza Clínica e Cirúrgica, bem como serviços complementares de diagnóstico, exceto qualquer tipo de atendimento hospitalar.\n
Parágrafo Único: Para atendimento de serviços hospitalares, o interessado deve procurar a Unidade mais próxima para avaliação, compra e formalização de instrumento contratual próprio.\n\n
Cláusula 2 - A VENDEDORA somente se responsabilizará pelo atendimento feito em suas unidades, e pelos cirurgiões dentistas de seu corpo clínico sendo que, qualquer espécie de consulta ou tratamento realizado por outros cirurgiões dentistas, isentará a mesma de quaisquer custos ou danos.\n\n
Cláusula 3 - A VENDEDORA se obriga a oferecer ao(s) COMPRADOR(ES), a partir deste ato, todo tratamento contratado, da seguinte forma: valor de R$ 275,00 (duzentos e setenta e cinco reais) para avaliação, atendimento, raio-x, exame complementar e documentações iniciais; valor de R$ 225,00 (duzentos e vinte e cinco reais) para profilaxia; valor de R$ 100,00 (cem reais) para instalação de aparelho ortodôntico; valor de R$ 49,00 (quarenta e nove reais) para cada dente restaurado em resina; valor de R$ 49,00 (quarenta e nove reais) para extrações, com exceção de terceiro molar; valor de R$ 49,00 (quarenta e nove reais) para tratamento periodontal (raspagem simples e subgengival); valor de R$ 300,00 (trezentos reais) para tratamento endodôntico (canal), por dente realizado.\n
Parágrafo Primeiro: A VENDEDORA fica obrigada a realizar os serviços odontológicos para o(s) COMPRADOR(ES), até o limite do valor deste contrato, descrito na Cláusula 6. Caso o(s) COMPRADOR(ES) queira realizar tratamentos que extrapolem o valor deste contrato, o montante excedente de referidos tratamentos poderá ser pago à parte e acrescentado nas parcelas descritas na Cláusula 6 deste instrumento.\n
Parágrafo Segundo: O(s) COMPRADOR(ES) fica(m) autorizado(s) a realizar seus tratamentos excedentes mesmo sem nova assinatura de contrato de compra e venda junto à VENDEDORA, desde que esta esteja ciente e autorize o parcelamento de tais tratamentos através de nota promissória devidamente assinada pelo(s) COMPRADOR(ES).\n
Parágrafo Terceiro: O procedimento da LIMPEZA inclui apenas a profilaxia e a raspagem; o procedimento do RAIO-X inclui apenas a modalidade simples; o procedimento da RESTAURAÇÃO não inclui serviços de estética e pós-canal; o procedimento de CANAL DE DENTE PERMANENTE inclui apenas um dente por pessoa; o procedimento da EXTRAÇÃO SIMPLES DE DENTE E RAIZ não inclui a extração dos dentes sisos; a APLICAÇÃO DE FLUOR E SELANTE se dará de forma normal, a INSTALAÇÃO DE APARELHO ORTODÔNTICO só será realizado após pagamento da 1ª (primeira) manutenção.\n\n
Cláusula 4 - Para as manutenções ortodônticas, o(s) COMPRADOR(ES) negociará(ão) valores com a VENDEDORA, após avaliação clínica, a qual definirá as necessidades de seu caso. Referidas manutenções ortodônticas serão pagas à parte bem como serão contratadas através de instrumento contratual próprio.\n\n
Cláusula 5 – Para todos os demais tratamentos não mencionados na cláusula 3, a VENDEDORA ficará obrigada a oferecer ao(s) COMPRADOR(ES), descontos de até 50% do valor da tabela praticada pela OdontoCompany.\n\n
Cláusula 6 – O(s) COMPRADOR(ES) se obriga(m) a pagar à VENDEDORA, pela compra expressa neste contrato, o valor total de R$ {carne} CARNÊ CLÍNICA\n
                         R$ {entrada} ENTRADA PIX\n
                         R$ {restante} RESTANTE\n\n
Parágrafo Único: Qualquer pagamento referente ao presente instrumento de compra e venda somente será aceito após o início do tratamento adquirido.\n\n
Cláusula 7 – Este contrato terá duração de 22 (vinte e dois) meses, a contar da data de sua assinatura. Encerrado referido prazo, sem pendências de pagamentos e tratamentos, automaticamente os direitos e obrigações do presente instrumento serão extintos.\n
Caso seja do interesse do(s) COMPRADOR(ES) proceder com nova compra, deverá(ão) comparecer na unidade VENDEDORA. Qualquer um do(s) COMPRADORES, seja vinculado ou principal, poderá realizar modificações contratuais, bem como a exclusão/adicionar demais COMPRADORES vinculados ou principal, mediante simples solicitação por telefone ou mensagem de aplicativo de texto nos telefones cadastrados para a VENDEDORA.\n
Parágrafo Único: Na hipótese do(s) COMPRADOR(es) cancelar este contrato antes de seu prazo previsto para término, deverá manifestar sua intenção, por escrito, na clínica VENDEDORA, momento em que será realizado um acerto de contas referente aos serviços já prestados. Caso o valor que já tenha sido pago for superior ao serviço realizado, a VENDEDORA se obriga a restituir o(s) COMPRADOR(ES) da diferença. Da mesma forma, caso os serviços até então prestados não estejam quitados, o(s) COMPRADOR(ES) se obriga a quitá-los no ato da rescisão deste instrumento.\n\n
Cláusula 8 - Em caso de desistência por parte do(s) COMPRADOR(es), a VENDEDORA resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10% a qual o paciente está ciente e de acordo com a mesma.\n
Parágrafo Primeiro: Se houver a desistência, a fase de planejamento dos tratamentos correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n\n
Cláusula 9 – Em caso de parcelamento da compra, o(s) COMPRADOR(ES) se compromete(m) a pagar em dia suas parcelas, conforme expresso no presente documento. O atraso do pagamento implicará em multa de 2% ao mês e juros de mora pelos dias de inadimplência, além de ter seu tratamento clínico bloqueado, até o pagamento do valor pendente.\n\n
Cláusula 10 – Em relação aos dados pessoais, a VENDEDORA se compromete a cumprir o quanto exigido pela LEI GERAL DE PROTEÇÃO DE DADOS (LGPD) – Lei nº 13.709/2018, conforme abaixo.\n
Parágrafo Primeiro: O(s) COMPRADOR(ES) neste ato dá(ão) seu consentimento e autoriza(m) a coleta de dados pessoais imprescindíveis a execução deste contrato, tendo sido informado quanto ao tratamento de dados que será realizado pela VENDEDORA, nos termos da Lei n° 13.709/2018, especificamente quanto a coleta dos seguintes dados:\n
Dados relacionados à sua identificação pessoal e de seus dependentes (compradores vinculados), como nome completo, RG, CPF, dentre outros dados básicos, a fim de que se garanta a fiel contratação pelo respectivo COMPRADOR(ES);\n
Dados relacionados ao endereço, telefone e e-mail do(s) COMPRADOR(ES) e de seus dependentes (compradores vinculados), para eventual necessidade de utilização da VENDEDORA de envio de documentos, notificações, boletos, carnês, renovação de contrato e outras garantias necessárias ao fiel cumprimento deste instrumento;\n
Dados descritos nos itens a) e b) acima de crianças e adolescentes, menores de 18 (dezoito) anos, quando estes fizerem parte do presente contrato. Neste ato, o pai ou responsável legal, ora COMPRADOR(ES), consente especificamente e autoriza a coleta de tais dados do(s) menor(es).\n
Parágrafo Segundo: Os dados coletados poderão ser utilizados para compartilhamento com a Franqueadora da marca Odontocompany; compartilhamento para órgãos de segurança, conforme solicitação legal pertinente; compartilhamento com autoridade administrativa e judicial no âmbito de suas competências com base no estrito cumprimento do dever legal; bem como com os órgãos de proteção ao crédito e empresa de cobrança, a fim de garantir a adimplência do(s) COMPRADOR(ES) perante esta VENDEDORA.\n
Parágrafo Terceiro: Os dados coletados com base no legítimo interesse do(s) COMPRADOR(ES), bem como para garantir a fiel execução do contrato por parte da VENDEDORA, fundamentam-se no artigo 7º da Lei 13.709/2018, razão pela qual as finalidades descritas na Cláusula 9, Parágrafo Segundo, não são exaustivas.\n
Parágrafo Quarto: A VENDEDORA informa que todos os dados pessoais solicitados e coletados são os estritamente necessários para os fins almejados neste contrato.\n
Parágrafo Quinto: O(s) COMPRADOR(ES) autoriza(m) o compartilhamento de seus dados, para os fins descritos nesta cláusula 9, com terceiros legalmente legítimos para defender os interesses da VENDEDORA bem como do(s) COMPRADOR(ES).\n
Parágrafo Sexto: O(s) COMPRADOR(ES) possui(em) o tempo determinado de 05 (cinco) anos para acesso aos próprios dados armazenados, podendo também solicitar a exclusão de dados que foram previamente coletados com seu consentimento.\n
Parágrafo Sétimo: A exclusão de dados será efetuada sem que haja prejuízo por parte da VENDEDORA, tendo em vista a necessidade de guarda de documentos pelo prazo mínimo determinado de 05 (cinco) anos, conforme lei civil, consumerista, e Código de Ética Odontológico. Caso o(s) COMPRADOR(ES) deseje(m) efetuar a revogação de algum dado, deverá preencher uma declaração nesse sentido, ciente que a revogação de determinados dados poderá importar em eventuais prejuízos na prestação de serviços.\n
Parágrafo Oitavo: O(s) COMPRADOR(ES) autoriza(m), neste mesmo ato, a guarda dos documentos (contratos, notas promissórias, documentos fiscais, notificações, orçamentos) - em que pese eles possuam dados pessoais - por parte da VENDEDORA a fim de que ela cumpra com o determinado nas demais normas que regulam o presente contrato, bem como para o cumprimento da obrigação legal nos termos do artigo 16, inciso I, da Lei 13.709/2018.\n
Parágrafo Nono: Em eventual vazamento indevido de dados a VENDEDORA se compromete a comunicar o(s) COMPRADOR(ES) sobre o ocorrido, bem como sobre qual o dado vertido.\n
Parágrafo Décimo: A VENDEDORA informa que a gerência de dados e a manutenção do registro das operações de tratamento de dados pessoais, ocorrerão através de um sistema que colherá e tratará os dados na forma da lei.\n
Parágrafo Décimo Primeiro: Em atendimento ao artigo 9º da Lei 13.709/2018, a COMPRADORA informa que sua identificação e contato telefônico, constam no Quadro Resumo do presente instrumento, especificamente no item “A”.\n
Parágrafo Décimo Segundo: O(s) COMPRADOR(ES) fica(m) ciente que o tratamento de seus dados pessoais é condição para o fornecimento dos serviços ora adquiridos e terá direito a obter da VENDEDORA, em relação aos seus dados pessoais por esta tratados, a qualquer momento e mediante requisição:\n
I - confirmação da existência de tratamento de dados;\n
II - acesso aos seus dados;\n
III - correção de seus dados incompletos, inexatos ou desatualizados;\n
IV - anonimização, bloqueio ou eliminação de dados desnecessários, excessivos ou tratados em desconformidade com o disposto na Lei 13.709/2018;\n
V - portabilidade de seus dados a outro fornecedor de serviço, mediante requisição expressa e observados os segredos comercial e industrial, de acordo com a regulamentação do órgão controlador;\n
VI - portabilidade dos dados a outro fornecedor de serviço, mediante requisição expressa, de acordo com a regulamentação da autoridade nacional, observados os segredos comercial e industrial;\n
VII - eliminação dos dados pessoais tratados com o seu consentimento, exceto nas hipóteses previstas no art. 16 da Lei 13.709/2018;\n
VIII - informação das entidades públicas e privadas com as quais a VENDEDORA realizou uso compartilhado de dados;\n
IX - informação sobre a possibilidade de não fornecer consentimento e sobre as consequências da negativa;\n
X - revogação do consentimento, nos termos do § 5º do art. 8º da Lei 13.709/2018.\n\n
Cláusula 11 – Em relação aos dados sensíveis, a VENDEDORA se compromete a cumprir o quanto exigido pela LEI GERAL DE PROTEÇÃO DE DADOS (LGPD) – Lei nº 13.709/2018, conforme abaixo.\n
Parágrafo Primeiro: Dado pessoal sensível é todo dado que diz respeito sobre origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou a organização de caráter religioso, filosófico ou político, dado referente à saúde ou à vida sexual, dado genético ou biométrico, quando vinculado a uma pessoa natural. No caso do presente contrato, uma vez que a VENDEDORA se trata de estabelecimento de saúde, precisará de dados relacionados à saúde do(s) COMPRADOR(ES) e de seus dependentes (compradores vinculados).\n
Parágrafo Segundo: Nos termos do artigo 11, inciso II, alínea “f)” da Lei 13.709/2018, não há necessidade de consentimento do(s) COMPRADOR(ES) acerca de seus dados sensíveis, uma vez que tais dados são indispensáveis para a tutela de sua saúde bucal, prestada por profissionais de saúde da VENDEDORA.\n\n
Cláusula 12 - Rescindido o contrato, os dados pessoais e sensíveis coletados serão armazenados pelo tempo determinado na cláusula 9ª, Parágrafo Sétimo. Passado o tempo de guarda pertinente, a VENDEDORA efetuará o descarte dos dados adequadamente, autorizada a conservação dos dados pelo(s) COMPRADOR(ES), para cumprimento de obrigação legal, perante o Código de Ética Odontológico; para uso exclusivo da VENDEDORA, com anonimação dos dados; para estudo por órgão de pesquisa; ou para outra hipótese prevista no artigo 16 da Lei 13.709/2018.\n\n
Cláusula 13 – A COMPRADORA (CONTRATANTE) declara que concorda e que está ciente que este contrato abrange apenas os procedimentos descritos na cláusula 3, e fica acordado entre as partes que a realização de quaisquer outros tratamentos irá ficar condicionada à realização de outro contrato, onde o inicio do tratamento só será realizado mediante pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n
Fica acordado que nestes outros contratos:\n
Parágrafo Primeiro: Fica acordado que a COMPRADORA (CONTRATANTE) poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
Parágrafo Segundo: A COMPRADORA (CONTRATANTE) irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter início.\n
Parágrafo Terceiro: Em caso de mais de 1 (um) procedimento, caberá ao VENDEDOR (CONTRATADO) realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do COMPRADOR (CONTRATANTE).\n\n
Cláusula 14 - Na hipótese do contratante abandonar a prestação de serviços por um período superior a 6 (seis) meses, será o equivalente ao fim do contrato por adimplemento total por parte da CONTRATADA, tendo em vista que o contratante deu causa ao abandono da prestação de serviços.\n
Parágrafo Primeiro - Nestes casos, o CONTRATANTE não terá a restituição dos valores pagos, pois foi este quem deu causa ao abandono do contrato, tendo o início da contagem do prazo na última consulta realizada ou último contato realizado entre as partes.\n
Parágrafo Segundo - Tem-se que inexistirá qualquer tipo de devolução de valores, pois a CONTRATADA teve inúmeros prejuízos com o abandono do contrato como a disponibilização de profissionais em especial para o atendimento do CONTRATANTE no tempo e no número de sessões exatas de acordo com o presente contrato, bem como a compra de materiais que foram perdidos pelo abandono da prestação de serviços.\n
Parágrafo Terceiro - Para fins de ‘’abandono’’ será considerada a ausência física nos atendimentos agendados, bem como a não realização de qualquer tipo de comunicação com a CONTRATADA para a realização de agendamentos e prosseguimento no tratamento, estando o CONTRATANTE ciente de sua total e exclusiva responsabilidade de promover as ligações e agendamentos para prosseguir com o tratamento.\n
Parágrafo Quarto - Para inexistir dispositivos abusivos, estando com o equilíbrio contratual devidamente inserido, será fornecido um prazo longo de 6 (seis) meses para considerar que houve o devido abandono da prestação de serviços.\n\n
Cláusula 15 - As partes concordam que em caso de falecimento da parte CONTRATANTE, serão cobrados todos os valores dos procedimentos já realizados e finalizados, com acréscimo da taxa da fase de planejamento e a multa rescisória de 10% (dez por cento).\n
Parágrafo Primeiro: Entende-se que a parte CONTRATADA não deu causa a qualquer motivo da rescisão, sendo, portanto, devido os valores da multa rescisória, dos procedimentos realizados, e dos gastos da clínica.\n
Parágrafo Segundo: A parte CONTRATANTE declara que o pagamento poderá ser realizado para qualquer herdeiro, que se responsabilizará pela repartição dos valores obtidos a título de rescisão.\n\n
Cláusula 16 - Por ser um produto/serviço de bem durável, entende-se que a garantia do tratamento será de 90 (noventa) dias a contar da data da entrega do produto ou finalização do tratamento.\n
Parágrafo Único: Em caso de repetição de procedimento por ser constatado algum desajuste no produto/serviço realizado, não irá ser contado o prazo da repetição para fim da garantia do serviço, mas sim o prazo de entrega do 1° produto/serviço.\n\n
Cláusula 17 - Ao assinar o termo de satisfação, a parte CONTRATANTE dará plena geral e irrevogável quitação dos serviços e produtos realizados pela clínica, não podendo posteriormente vir a solicitar repetição do serviço/produto realizado por termos funcionais e estéticos, bem como renuncia a interpelação judicial de danos materiais e morais.\n\n
Cláusula 18 - Ao ser constatado algum desajuste ou necessidade de reparo do produto/serviço antes do fim da garantia de 90 (noventa) dias, deverá a parte CONTRATANTE oportunizar a repetição do trabalho/ajuste pela própria clínica.\n
Parágrafo Primeiro: Se a parte CONTRATANTE não tiver mais ânimo na realização de ajustes ou repetição do trabalho, deverá arcar com os custos de todos os procedimentos e da taxa da fase de planejamento e multa rescisória de 10% (dez por cento), independentemente da existência de culpa/erro/imperícia, pois a parte CONTRATADA irá fornecer os materiais e profissionais para correção dos procedimentos de forma gratuita.\n\n
Cláusula 19 - A parte CONTRATANTE aceita desde a assinatura deste instrumento, que para fins de rescisão, concorda com os cálculos e demonstrativos que serão apresentados pela parte CONTRATADA.\n\n
Claúsula 20 - Em virtude de intercorrências no tratamento, a parte CONTRATADA se responsabilizará pela correção dos produtos/serviços entregues que estejam dentro da garantia de 90 (noventa) dias, contudo, fica vedado à parte CONTRATANTE exigir a devolução integral dos valores e/ou pagamento de outra clínica, em vista da necessidade de oportunizar os reparos dos procedimentos/serviços.\n\n
Cláusula 21 - Se ao iniciar um tratamento específico, for constatado pelos profissionais odontólogos da parte CONTRATADA mediante à avaliação posterior ou exames posteriores que a parte CONTRATANTE deverá realizar outros procedimentos que não foram pactuados de início, fica estabelecido que estes procedimentos/serviços não fazem parte do tratamento originário devendo ser pagos os valores diferencias dos outros procedimentos.\n
Parágrafo Único: Se o prosseguimento do tratamento for impossibilitado pela necessidade destes outros procedimentos, a parte CONTRATANTE poderá solicitar a rescisão onde pagará por todos os custos e os procedimentos realizados e as multas rescisórias, ou pactuar novo contrato com a parte CONTRATADA para realização destes novos procedimentos.\n\n
Cláusula 22 - Para dirimir quaisquer controvérsias oriundas deste instrumento, será competente o foro da Comarca de .\n\n
Para fins de esclarecimento, fica expresso que o presente Contrato de Compra e Venda de Serviços Odontológicos não é Plano de Saúde. Trata-se de uma forma de venda pré-paga e/ou pós-paga de serviços odontológicos, que assegura ao(s) COMPRADOR(ES) apenas os serviços, preços e descontos aqui expressos.\n\n
E por estarem assim, justos e contratados, assinam as partes o presente Contrato de Compra e Venda de Serviços Odontológicos, na presença de duas testemunhas.\n

{assinaturas}


        """

    # *************************************************************************************

    #                   CONTRATO PREENCHIMENTO ONEROSA

    # *************************************************************************************


    elif contract_option == "Contrato Preenchimento":
        anestesia = st.text_input("Tipo de anestesia utilizada")
        regiao_aplicacao = st.text_input("Região para aplicação de ácido hialurônico")
        valor_vista = st.text_input("Valor total à vista (R$)")
        data_vista = st.text_input("Data de pagamento à vista")
        valor_sinal = st.text_input("Valor do sinal (R$)")
        data_sinal = st.text_input("Data de pagamento do sinal")
        parcelas = st.text_input("Número de parcelas")
        valor_parcela = st.text_input("Valor de cada parcela (R$)")
        vencimento_parcelas = st.text_input("Data de vencimento das parcelas")
        multa_mora = st.text_input("Multa por atraso (%)")
        juros = st.text_input("Juros mensais (%)")
        resto_pagamento = st.text_input("Descrição das condições para o pagamento restante")


        contract_text = f"""


        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:\n\n
I – Fase de Orientação:\n
O paciente será, nesta fase, orientado a respeito do que é a aplicação de ácido hialurônico e que tal substância é encontrada em todos os seres humanos, animais e em plantas. Os produtos utilizados para harmonizar o volume facial, ou preencher sulcos, são resultantes de fermentação biológica, sendo altamente purificados e hipoalergênicos. Tal procedimento é indicado para melhorar a hidratação da pele, preencher sulcos faciais e readequar volumes faciais.\n
O paciente recebe aplicação das suas diversas técnicas, do tratamento, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente. Nesta fase o paciente tomará ciência dos possíveis sintomas pós procedimento. Será informado também sobre o tratamento necessário após a realização da cirurgia e os motivos pelos quais será adotado o tratamento proposto.\n
Parágrafo único – O paciente ficará esclarecido e ciente de que a natureza deste tratamento objetiva a aplicação de ácido hialurônico na face e possui natureza estética, com obrigação de meio e de resultado, dependendo do caso.\n\n
II – Fase de Planejamento:\n
Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.\n
Parágrafo único: Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento.\n\n
III – Fase cirúrgica:\n
Anestesia {anestesia} aplicação de ácido hialurônico na região {regiao_aplicacao}.\n\n
IV - Tratamento:\n
O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento.\n
Parágrafo único - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião e pela clínica, ou por sua ausência nas consultas marcadas, o cirurgião e a clínica ficarão isentos de responsabilidade sobre este tratamento. Existe a possibilidade de infeccionar e formar um abscesso no local da cirurgia, caso não cumprida as consultas marcadas e orientações do dentista.\n\n
V - Dos “Retoques”:\n
É sabido, pelo paciente, que procedimentos cirúrgicos posteriores ao serviço realizado (ditos “retoques”) podem ser necessários. Em qualquer tipo de cirurgia este fato é bastante comum. Daí, custos de anestesia, internação (gastos com clínica ou hospital) e se necessário dentista auxiliar e instrumentadora serão debitados ao paciente, não havendo, entretanto, cobrança de honorários pela Clínica.\n
Parágrafo Primeiro - não será considerado retoque as consequências de não cuidados da paciente em relação ao pós-operatório.\n
Parágrafo Segundo - no caso de qualquer reação que seja necessário a retirada do produto as despesas relativas a tais procedimentos serão debitadas ao paciente, assim como a sua posterior colocação e compra de novos produtos.\n
Parágrafo Terceiro - é de responsabilidade do paciente informar com antecedência sobre tabagismo, uso de drogas ilícitas, uso de medicamentos como Roacutan, antidepressivos, anticoagulantes, ou qualquer outro de uso contínuo.\n
Parágrafo Quarto - não há aplicação de pontos extras (retoques) em ácido hialurônico. Novos pontos de aplicação que venham a ser necessários serão cobrados.\n
Parágrafo Quinto - não há retoque de aplicação em função da resposta particular de cada organismo à aplicação, podendo ser reabsorvido completamente. O valor é cobrado por aplicação. Caso o paciente queira nova aplicação será cobrado valor integral.\n
Parágrafo Sexto - não há retoque para preenchimentos. O valor cobrado corresponde à aplicação do produto e o volume a ser aplicado em uma sessão nem sempre é suficiente para corrigir as rugas e depressões que o paciente anseia, desta forma mais produto é necessário e procedimento integral será cobrado.\n\n
VI - Do pagamento:\n
A remuneração pecuniária do tratamento ora proposto, será da seguinte maneira:\n
À vista: R$ {valor_vista} data {data_vista}\n
À prazo/sinal: R$ {valor_sinal} data {data_sinal} e o restante em {parcelas} parcelas no valor de {valor_parcela} com vencimento nos dias {vencimento_parcelas}. Peculiaridades em relação ao meio de pagamento: {resto_pagamento} \n
Parágrafo 1º - O paciente concorda que os pagamentos vencidos e efetuados fora dos prazos previstos anteriormente estarão sujeitos a multa de mora {multa_mora} % e juros de {juros} % ao mês.\n
Parágrafo segundo - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o(a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.\n\n
VII – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10% a qual o paciente está ciente e de acordo com a mesma. Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.\n\n
VIII – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n\n
IX – A responsabilidade do cirurgião dentista e da clínica baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.\n\n
X – O paciente, neste ato, doa todo o material de diagnóstico e planejamento (radiografias, modelos, slides, exames complementares) trazido pelo mesmo ou obtido durante o tratamento o qual passa a ser propriedade e documento da clínica, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica serão arquivados com a clínica.\n\n
XI – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n\n
XII - Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.\n
Parágrafo primeiro – Fica acordado que o CONTRATANTE poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
Parágrafo segundo – O CONTRATANTE irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter início.\n
Parágrafo terceiro – Em caso de mais de 1 (um) procedimento, caberá ao CONTRATADO realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do CONTRATANTE.\n\n
XIII – Em relação aos dados pessoais, a clínica se compromete a cumprir o quanto exigido pela LEI GERAL DE PROTEÇÃO DE DADOS (LGPD) – Lei nº 13.709/2018, conforme abaixo.\n
Parágrafo primeiro – O paciente neste ato dá seu consentimento e autoriza a coleta de dados pessoais imprescindíveis a execução deste contrato, tendo sido informado quanto ao tratamento de dados que será realizado pela clínica, nos termos da Lei n° 13.709/2018, especificamente quanto a coleta dos seguintes dados:\n
a) Dados relacionados à sua identificação pessoal e de seus dependentes, como nome completo, RG, CPF, dentre outros dados básicos, a fim de que se garanta a fiel contratação pelo respectivo paciente;\n
b) Dados relacionados ao endereço, telefone e e-mail do paciente para eventual necessidade de utilização da clínica de envio de documentos, notificações, boletos, carnês, renovação de contrato e outras garantias necessárias ao fiel cumprimento deste instrumento;\n
c) Dados descritos nos itens a) e b) acima de crianças e adolescentes, menores de 18 (dezoito) anos, quando estes fizerem parte do presente contrato. Neste ato, o pai ou responsável legal consente especificamente e autoriza a coleta de tais dados do(s) menor(es).\n
Parágrafo segundo - Os dados coletados poderão ser utilizados para compartilhamento com a Franqueadora da marca Odontocompany; compartilhamento para órgãos de segurança, conforme solicitação legal pertinente; compartilhamento com autoridade administrativa e judicial no âmbito de suas competências com base no estrito cumprimento do dever legal; bem como com os órgãos de proteção ao crédito e empresa de cobrança, a fim de garantir a adimplência do paciente.\n
Parágrafo terceiro - Os dados coletados com base no legítimo interesse do paciente, bem como para garantir a fiel execução do contrato por parte da clínica, fundamentam-se no artigo 7º da Lei 13.709/2018, razão pela qual as finalidades descritas na Cláusula VIII, Parágrafo Segundo, não são exaustivas.\n
Parágrafo quarto - A clínica informa que todos os dados pessoais solicitados e coletados são os estritamente necessários para os fins almejados neste contrato.\n
Parágrafo quinto – O paciente autoriza o compartilhamento de seus dados, para os fins descritos nesta cláusula, com terceiros legalmente legítimos para defender os interesses da clínica bem como do paciente.\n
Parágrafo sexto – O paciente possui o tempo determinado de 05 (cinco) anos para acesso aos próprios dados armazenados, podendo também solicitar a exclusão de dados que foram previamente coletados com seu consentimento.\n
Parágrafo sétimo - A exclusão de dados será efetuada sem que haja prejuízo por parte da clínica, tendo em vista a necessidade de guarda de documentos pelo prazo mínimo determinado de 05 (cinco) anos, conforme lei civil, consumerista, e Código de Ética Odontológico. Caso o paciente deseje efetuar a revogação de algum dado, deverá preencher uma declaração nesse sentido, ciente que a revogação de determinados dados poderá importar em eventuais prejuízos na prestação de serviços.\n
Parágrafo oitavo – O paciente autoriza, neste mesmo ato, a guarda dos documentos (contratos, notas promissórias, documentos fiscais, notificações, orçamentos) - em que pese eles possuam dados pessoais - por parte da clínica a fim de que ela cumpra com o determinado nas demais normas que regulam o presente contrato, bem como para o cumprimento da obrigação legal nos termos do artigo 16, inciso I, da Lei 13.709/2018.\n
Parágrafo nono - Em eventual vazamento indevido de dados a clínica se compromete a comunicar o paciente sobre o ocorrido, bem como sobre qual o dado vertido.\n
Parágrafo décimo - A clínica informa que a gerência de dados e a manutenção do registro das operações de tratamento de dados pessoais, ocorrerão através de um sistema que colherá e tratará os dados na forma da lei.\n
Parágrafo décimo primeiro - Em atendimento ao artigo 9º da Lei 13.709/2018, a clínica informa que sua identificação e contato telefônico, constam no primeiro parágrafo do presente instrumento.\n
Parágrafo décimo segundo: O paciente fica ciente que o tratamento de seus dados pessoais é condição para o fornecimento dos serviços ora adquiridos e terá direito a obter da clínica, em relação aos seus dados pessoais por esta tratados, a qualquer momento e mediante requisição:\n
I - confirmação da existência de tratamento de dados;\n
II - acesso aos seus dados;\n
III - correção de seus dados incompletos, inexatos ou desatualizados;\n
IV - anonimização, bloqueio ou eliminação de dados desnecessários, excessivos ou tratados em desconformidade com o disposto na Lei 13.709/2018;\n
V - portabilidade de seus dados a outro fornecedor de serviço, mediante requisição expressa e observados os segredos comercial e industrial, de acordo com a regulamentação do órgão controlador;\n
VI - eliminação dos dados pessoais tratados com o seu consentimento, exceto nas hipóteses previstas no art. 16 da Lei 13.709/2018;\n
VII - informação das entidades públicas e privadas com as quais a clínica realizou uso compartilhado de dados;\n
VIII - informação sobre a possibilidade de não fornecer consentimento e sobre as consequências da negativa;\n
IX - revogação do consentimento, nos termos do § 5º do art. 8º da Lei 13.709/2018.\n\n
XIV – Em relação aos dados sensíveis:\n
A clínica se compromete a cumprir o quanto exigido pela LEI GERAL DE PROTEÇÃO DE DADOS (LGPD) – Lei nº 13.709/2018, conforme abaixo.\n
Parágrafo primeiro - Dado pessoal sensível é todo dado que diz respeito sobre origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou a organização de caráter religioso, filosófico ou político, dado referente à saúde ou à vida sexual, dado genético ou biométrico, quando vinculado a uma pessoa natural. No caso do presente contrato, uma vez que a clínica se trata de estabelecimento de saúde, precisará de dados relacionados à saúde do paciente.\n
Parágrafo segundo - Nos termos do artigo 11, inciso II, alínea “f)” da Lei 13.709/2018, não há necessidade de consentimento do paciente acerca de seus dados sensíveis, uma vez que tais dados são indispensáveis para a tutela de sua saúde, prestada por profissionais de saúde da clínica.\n\n
XV - Rescindido o contrato:\n
Os dados pessoais e sensíveis coletados serão armazenados pelo tempo determinado na cláusula VIII, Parágrafo Sétimo. Passado o tempo de guarda pertinente, a clínica efetuará o descarte dos dados adequadamente, autorizada a conservação dos dados pelo paciente, para cumprimento de obrigação legal, perante o Código de Ética Odontológico; para uso exclusivo da clínica, com anonimação dos dados; para estudo por órgão de pesquisa; ou para outra hipótese prevista no artigo 16 da Lei 13.709/2018.\n\n
O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.\n
As partes elegem o Foro da Comarca de Anápolis/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, ainda que mais favorável for.\n

{assinaturas}


        """

    # *************************************************************************************

    #                   CONTRATO PROCEDIMENTOS GERAIS

    # *************************************************************************************


    elif contract_option == "Contrato Procedimentos Gerais":
        restauracao = st.text_input("Indique se há necessidade de restauração simples")
        profilaxia = st.text_input("Informe o valor total à vista para profilaxia simples (R$)")
        raspagem = st.text_input("Data prevista para pagamento da raspagem simples")
        extracao = st.text_input("Informe o valor do sinal para extração simples (R$)")
        clareamento = st.text_input("Data do pagamento para clareamento")
        valor_vista = st.text_input("Número de parcelas para o pagamento total")
        
        contract_text = f"""


        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou CONTRATANTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:\n\n
DOS SERVIÇOS CONTRATADOS:\n\n
Assinalar com X no campo dos serviços pactuados.\n
{restauracao} RESTAURAÇÃO SIMPLES\n
{profilaxia} PROFILAXIA SIMPLES\n
{raspagem} RASPAGEM SIMPLES\n
{extracao} EXTRAÇÃO SIMPLES\n
{clareamento} CLAREAMENTO\n\n
VALOR TOTAL: {valor_vista}\n\n\n\n
I – Fase de Orientação:\n
O paciente será, nesta fase, orientado a respeito do que são o/os procedimento(s) contratado(s) de acordo com as marcações acima, das suas diversas técnicas, do tratamento, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente. Nesta fase o paciente tomará ciência dos possíveis sintomas pós procedimento(s). Será informado também sobre o tratamento necessário após a realização da cirurgia e os motivos pelos quais será adotado o tratamento proposto.\n
Parágrafo único – O paciente ficará esclarecido e ciente, dando plena concordância de que a natureza deste tratamento é a realização de um procedimento cirúrgico, não havendo qualquer promessa de resultado, sendo uma obrigação de meio.\n\n
II – Fase de Planejamento:\n
Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.\n
Parágrafo único - Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento.\n\n
III – Fase cirúrgica:\n
Realização dos procedimentos pactuados descritos nos SERVIÇOS CONTRATADOS.\n\n
IV - Tratamento:\n
O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento.\n
Parágrafo único - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião e pela clínica, ou por sua ausência nas consultas marcadas, o cirurgião e a clínica ficarão isentos de responsabilidade sobre este tratamento. Existe a possibilidade de infeccionar e formar um abscesso no local da cirurgia, caso não cumprida as consultas marcadas e orientações do dentista.\n\n
V - Do pagamento:\n
A remuneração pecuniária do tratamento ora proposto, será da seguinte maneira:\n
VALOR:\n\n
Parágrafo primeiro - O paciente concorda que os pagamentos vencidos e efetuados fora dos prazos previstos anteriormente estarão sujeitos a multa de mora _____% e juros de ______% ao mês.\n
Parágrafo segundo - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o(a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.\n
Parágrafo terceiro - Se o paciente optar pela realização de pagamentos que envolvem instituições financeiras/administradoras de cartões de crédito de terceiros, concorda e está ciente que a clínica é parte totalmente ilegítima em relação a débitos/cobranças/negativações realizadas por estas empresas.\n
Parágrafo quarto - Nos termos do parágrafo 3°, o paciente renuncia a qualquer interpelação judicial em face da clínica em relação a débitos/cobranças/negativações realizadas por empresas de crédito de terceiros, tanto em danos materiais, quanto danos morais.\n
Parágrafo quinto - Se o paciente (CONTRATANTE) realizar financiamento junto à instituições financeiras para custear seu tratamento e posteriormente requerer a rescisão, este ficará responsável pelo ressarcimento ao CONTRATADO das taxas/juros/multas que serão cobrados pelas instituições financeiras no ato de rescisão junto a estas. Os valores serão abatidos na constância da rescisão do CONTRATANTE com o CONTRATADO, se houver saldo no tratamento, ou se não, deverão ser pagos pelo PACIENTE (CONTRATANTE) para o CONTRATADO no ato da rescisão com o CONTRATANTE.\n
Parágrafo sexto - Os valores do parágrafo 5° serão deduzidos através do pagamento do boleto de rescisão do financiamento em diferença da quantia paga pelo paciente, ou simples demonstrativo do contrato de financiamento.\n\n
VI – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10% a qual o paciente está ciente e de acordo com a mesma. Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.\n\n
VII – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n\n
VIII – A responsabilidade do cirurgião dentista e da clínica baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.\n\n
IX – O paciente, neste ato, doa todo o material de diagnóstico e planejamento (radiografias, modelos, slides, exames complementares) trazido pelo mesmo ou obtido durante o tratamento o qual passa a ser propriedade e documento da clínica, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica serão arquivados com a clínica.\n\n
X – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n\n
XI - Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.\n
Parágrafo primeiro – Fica acordado que o contratante (paciente) poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
Parágrafo segundo – O contratante (paciente) irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter início.\n
Parágrafo terceiro – Em caso de mais de 1 (um) procedimento, caberá à contratada (clínica) realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do contratante (paciente).\n\n
XI - Na hipótese de o contratante (paciente) abandonar a prestação de serviços por um período superior a 6 (seis) meses, será o equivalente ao fim do contrato por adimplemento total por parte da contratada (clínica), tendo em vista que o contratante (paciente) deu causa ao abandono da prestação de serviços.\n
Parágrafo primeiro - Nestes casos, o contratante (paciente) não terá a restituição dos valores pagos, pois foi este quem deu causa ao abandono do contrato, tendo o início da contagem do prazo na última consulta realizada ou o último contato realizado entre as partes.\n
Parágrafo segundo - Tem-se que inexistirá qualquer tipo de devolução de valores, pois a contratada (clínica) teve inúmeros prejuízos com o abandono do contrato como a disponibilização de profissionais em especial para o atendimento do contratante (paciente) no tempo e no número de sessões exatas de acordo com o presente contrato, bem como a compra de materiais que foram perdidos pelo abandono da prestação de serviços.\n
Parágrafo terceiro - Para fins de ‘’abandono’’ será considerada a ausência física nos atendimentos agendados, bem como a não realização de qualquer tipo de comunicação com a contratada (clínica) para a realização de agendamentos e prosseguimento no tratamento, estando o contratante (paciente) ciente de sua total e exclusiva responsabilidade de promover as ligações e agendamentos para prosseguir com o tratamento.\n
Parágrafo quarto - Para inexistir dispositivos abusivos, estando com o equilíbrio contratual devidamente inserido, será fornecido um prazo longo de 6 (seis) meses para considerar que houve o devido abandono da prestação de serviços.\n\n
XII - As partes concordam que em caso de falecimento do paciente, serão cobrados todos os valores dos procedimentos já realizados e finalizados, com acréscimo da taxa da fase de planejamento e a multa rescisória de 10% (dez por cento).\n
Parágrafo primeiro - Entende-se que a clínica (contratada) não deu causa a qualquer motivo da rescisão, sendo, portanto, devido os valores da multa rescisória, dos procedimentos realizados, e dos gastos da clínica.\n
Parágrafo segundo – O paciente declara que o pagamento poderá ser realizado para qualquer herdeiro, que se responsabilizará pela repartição dos valores obtidos a título de rescisão.\n\n
XIII - Por ser um produto/serviço de bem durável, entende-se que a garantia do tratamento será de 90 (noventa) dias a contar da data da entrega do produto ou finalização do tratamento.\n
Parágrafo único - Em caso de repetição de procedimento por ser constatado algum desajuste no produto/serviço realizado, não irá ser contado o prazo da repetição para fim da garantia do serviço, mas sim o prazo de entrega do 1° produto/serviço.\n\n
XIV - Ao assinar o termo de satisfação, o paciente dará plena geral e irrevogável quitação dos serviços e produtos realizados pela clínica, não podendo posteriormente vir a solicitar repetição do serviço/produto realizado por termos funcionais e estéticos, bem como renuncia a interpelação judicial de danos materiais e morais.\n\n
XV - Ao ser constatado algum desajuste ou necessidade de reparo do produto/serviço antes do fim da garantia de 90 (noventa) dias, deverá o paciente oportunizar a repetição do trabalho/ajuste pela própria clínica.\n
Parágrafo primeiro - Se o paciente não tiver mais ânimo na realização de ajustes ou repetição do trabalho, deverá arcar com os custos de todos os procedimentos e da taxa da fase de planejamento e multa rescisória de 10% (dez por cento), independentemente da existência de culpa/erro/imperícia, pois a clínica (contratada) irá fornecer os materiais e profissionais para correção dos procedimentos de forma gratuita.\n\n
XVI – O paciente aceita desde a assinatura deste instrumento, que para fins de rescisão, concorda com os cálculos e demonstrativos que serão apresentados pela parte CONTRATADA.\n\n
XVII - Em virtude de intercorrências no tratamento, a clínica (contratada) se responsabilizará pela correção dos produtos/serviços entregues que estejam dentro da garantia de 90 (noventa) dias, contudo, fica vedado ao paciente exigir a devolução integral dos valores e/ou pagamento de outra clínica, em vista da necessidade de oportunizar os reparos dos procedimentos/serviços.\n\n
XVIII - Se ao iniciar um tratamento específico, for constatado pelos profissionais odontólogos da clínica (contratada) mediante à avaliação posterior ou exames posteriores que o paciente deverá realizar outros procedimentos que não foram pactuados de início, fica estabelecido que estes procedimentos/serviços não fazem parte do tratamento originário devendo ser pagos os valores diferenciais dos outros procedimentos.\n
Parágrafo único - Se o prosseguimento do tratamento for impossibilitado pela necessidade destes outros procedimentos, o paciente poderá solicitar a rescisão onde pagará por todos os custos e os procedimentos realizados e as multas rescisórias, ou pactuar novo contrato com a clínica (contratada) para realização destes novos procedimentos.\n\n
XIX – Em relação aos dados pessoais, a clínica se compromete a cumprir o quanto exigido pela LEI GERAL DE PROTEÇÃO DE DADOS (LGPD) – Lei nº 13.709/2018, conforme abaixo.\n
Parágrafo primeiro – O paciente neste ato dá seu consentimento e autoriza a coleta de dados pessoais imprescindíveis a execução deste contrato, tendo sido informado quanto ao tratamento de dados que será realizado pela clínica, nos termos da Lei n° 13.709/2018, especificamente quanto a coleta dos seguintes dados:\n
a) Dados relacionados à sua identificação pessoal e de seus dependentes, como nome completo, RG, CPF, dentre outros dados básicos, a fim de que se garanta a fiel contratação pelo respectivo paciente;\n
b) Dados relacionados ao endereço, telefone e e-mail do paciente para eventual necessidade de utilização da clínica de envio de documentos, notificações, boletos, carnês, renovação de contrato e outras garantias necessárias ao fiel cumprimento deste instrumento;\n
c) Dados descritos nos itens a) e b) acima de crianças e adolescentes, menores de 18 (dezoito) anos, quando estes fizerem parte do presente contrato. Neste ato, o pai ou responsável legal consente especificamente e autoriza a coleta de tais dados do(s) menor(es).\n
Parágrafo segundo - Os dados coletados poderão ser utilizados para compartilhamento com a Franqueadora da marca Odontocompany; compartilhamento para órgãos de segurança, conforme solicitação legal pertinente; compartilhamento com autoridade administrativa e judicial no âmbito de suas competências com base no estrito cumprimento do dever legal; bem como com os órgãos de proteção ao crédito e empresa de cobrança, a fim de garantir a adimplência do paciente.\n
Parágrafo terceiro - Os dados coletados com base no legítimo interesse do paciente, bem como para garantir a fiel execução do contrato por parte da clínica, fundamentam-se no artigo 7º da Lei 13.709/2018, razão pela qual as finalidades descritas na Cláusula VIII, Parágrafo Segundo, não são exaustivas.\n
Parágrafo quarto - A clínica informa que todos os dados pessoais solicitados e coletados são os estritamente necessários para os fins almejados neste contrato.\n
Parágrafo quinto – O paciente autoriza o compartilhamento de seus dados, para os fins descritos nesta cláusula, com terceiros legalmente legítimos para defender os interesses da clínica bem como do paciente.\n
Parágrafo sexto – O paciente possui o tempo determinado de 05 (cinco) anos para acesso aos próprios dados armazenados, podendo também solicitar a exclusão de dados que foram previamente coletados com seu consentimento.\n
Parágrafo sétimo - A exclusão de dados será efetuada sem que haja prejuízo por parte da clínica, tendo em vista a necessidade de guarda de documentos pelo prazo mínimo determinado de 05 (cinco) anos, conforme lei civil, consumerista, e Código de Ética Odontológico. Caso o paciente deseje efetuar a revogação de algum dado, deverá preencher uma declaração nesse sentido, ciente que a revogação de determinados dados poderá importar em eventuais prejuízos na prestação de serviços.\n
Parágrafo oitavo – O paciente autoriza, neste mesmo ato, a guarda dos documentos (contratos, notas promissórias, documentos fiscais, notificações, orçamentos) - em que pese eles possuam dados pessoais - por parte da clínica a fim de que ela cumpra com o determinado nas demais normas que regulam o presente contrato, bem como para o cumprimento da obrigação legal nos termos do artigo 16, inciso I, da Lei 13.709/2018.\n
Parágrafo nono - Em eventual vazamento indevido de dados a clínica se compromete a comunicar o paciente sobre o ocorrido, bem como sobre qual o dado vertido.\n
Parágrafo décimo - A clínica informa que a gerência de dados e a manutenção do registro das operações de tratamento de dados pessoais, ocorrerão através de um sistema que colherá e tratará os dados na forma da lei.\n
Parágrafo décimo primeiro - Em atendimento ao artigo 9º da Lei 13.709/2018, a clínica informa que sua identificação e contato telefônico, constam no primeiro parágrafo do presente instrumento.\n
Parágrafo décimo segundo: O paciente fica ciente que o tratamento de seus dados pessoais é condição para o fornecimento dos serviços ora adquiridos e terá direito a obter da clínica, em relação aos seus dados pessoais por esta tratados, a qualquer momento e mediante requisição:\n
I - confirmação da existência de tratamento de dados;\n
II - acesso aos seus dados;\n
III - correção de seus dados incompletos, inexatos ou desatualizados;\n
IV - anonimização, bloqueio ou eliminação de dados desnecessários, excessivos ou tratados em desconformidade com o disposto na Lei 13.709/2018;\n
V - portabilidade de seus dados a outro fornecedor de serviço, mediante requisição expressa e observados os segredos comercial e industrial, de acordo com a regulamentação do órgão controlador;\n
VI - eliminação dos dados pessoais tratados com o seu consentimento, exceto nas hipóteses previstas no art. 16 da Lei 13.709/2018;\n
VII - informação das entidades públicas e privadas com as quais a clínica realizou uso compartilhado de dados;\n
VIII - informação sobre a possibilidade de não fornecer consentimento e sobre as consequências da negativa;\n
IX - revogação do consentimento, nos termos do § 5º do art. 8º da Lei 13.709/2018.\n\n
XX – Em relação aos dados sensíveis, a clínica se compromete a cumprir o quanto exigido pela LEI GERAL DE PROTEÇÃO DE DADOS (LGPD) – Lei nº 13.709/2018, conforme abaixo.\n
Parágrafo primeiro - Dado pessoal sensível é todo dado que diz respeito sobre origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou a organização de caráter religioso, filosófico ou político, dado referente à saúde ou à vida sexual, dado genético ou biométrico, quando vinculado a uma pessoa natural. No caso do presente contrato, uma vez que a clínica se trata de estabelecimento de saúde, precisará de dados relacionados à saúde do paciente.\n
Parágrafo segundo - Nos termos do artigo 11, inciso II, alínea “f)” da Lei 13.709/2018, não há necessidade de consentimento do paciente acerca de seus dados sensíveis, uma vez que tais dados são indispensáveis para a tutela de sua saúde, prestada por profissionais de saúde da clínica.\n\n
XXI - Rescindido o contrato, os dados pessoais e sensíveis coletados serão armazenados pelo tempo determinado do contrato. Passado o tempo de guarda pertinente, a clínica efetuará o descarte dos dados adequadamente, autorizada a conservação dos dados pelo paciente, para cumprimento de obrigação legal, perante o Código de Ética Odontológico; para uso exclusivo da clínica, com anonimação dos dados; para estudo por órgão de pesquisa; ou para outra hipótese prevista no artigo 16 da Lei 13.709/2018.\n\n
O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.\n
As partes elegem o Foro da Comarca de Anápolis/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, ainda que mais favorável for.\n

{assinaturas}


        """

    # *************************************************************************************

    #                   CONTRATO PROTESE ONEROSA

    # *************************************************************************************


    elif contract_option == "Contrato Prótese":
        valor_vista = st.text_input("Informe o valor total a ser pago à vista (R$)")
        data_vista = st.text_input("Data prevista para o pagamento à vista")
        valor_sinal = st.text_input("Valor do sinal inicial (R$)")
        data_sinal = st.text_input("Data do pagamento do sinal")
        parcelas = st.text_input("Número de parcelas para o pagamento restante")
        valor_parcela = st.text_input("Valor de cada parcela (R$)")
        vencimento_parcelas = st.text_input("Data de vencimento de cada parcela")
        multa_mora = st.text_input("Percentual da multa de mora por atraso (%)")
        juros = st.text_input("Percentual de juros ao mês para atrasos (%)")
        resto_pagamento = st.text_input("Especifique como o pagamento será dividido")

        contract_text = f"""


        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:\n\n
I – Fase de Orientação:\n
O paciente será, nesta fase, orientado a respeito do que são próteses, das suas diversas técnicas, do tratamento, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente.\n
Parágrafo 1º – O paciente ficará esclarecido e ciente de que a natureza deste tratamento objetiva a recuperação da função mastigatória.\n\n
II – Fase de Planejamento:\n
Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.\n
Parágrafo único: Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento.\n\n
III – Tratamento:\n
O dentista informará ao paciente neste momento qual o plano de tratamento e qual a prótese indicada para o seu caso. (escrever as próteses que serão realizadas), e quantas sessões serão necessárias. O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento.\n
Parágrafo 1º - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião, ou por sua ausência nas consultas marcadas, o cirurgião ficará isento de responsabilidade sobre as próteses. Nestes casos, a recolocação da prótese ficará a critério do cirurgião dentista.\n
Parágrafo 2º - O paciente fica consciente de que, em alguns casos, não será possível a recolocação da prótese, sendo neste caso proposto outro tipo de tratamento.\n\n
IV – Do pagamento:\n
À vista: R$ {valor_vista} data {data_vista}\n
À prazo/sinal: R$ {valor_sinal} data {data_sinal} e o restante em {parcelas} parcelas no valor de {valor_parcela} com vencimento nos dias {vencimento_parcelas}. Peculiaridades em relação ao meio de pagamento: {resto_pagamento} \n
Parágrafo 1º - O paciente concorda que os pagamentos vencidos e efetuados fora dos prazos previstos anteriormente estarão sujeitos a multa de mora {multa_mora} % e juros de {juros} % ao mês.\n
Parágrafo 2º - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o(a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.\n\n
V – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10% a qual o paciente está ciente e de acordo com a mesma. Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.\n\n
VI – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n\n
VII – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n\n
VIII - Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.\n
Parágrafo 1º – Fica acordado que o CONTRATANTE poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
Parágrafo 2º – O CONTRATANTE irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter início.\n
Parágrafo 3º – Em caso de mais de 1 (um) procedimento, caberá ao CONTRATADO realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do CONTRATANTE.\n\n
VIII – A responsabilidade do cirurgião dentista baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.\n\n
IX – O paciente, neste ato, doa todo o material de diagnóstico e planejamento (radiografias, modelos, slides, exames complementares) trazido pelo mesmo ou obtido durante o tratamento o qual passa a ser propriedade e documento do cirurgião dentista, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica serão arquivados com o cirurgião dentista.\n\n
O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.\n\n
As partes elegem o Fórum da Comarca de Anápolis/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, ainda que mais favorável for.\n

{assinaturas}


        """

    # *************************************************************************************

    #                   CONTRATO IMPLANTES ONEROSA

    # *************************************************************************************


    elif contract_option == "Contrato Implantes":
        enxerto = st.text_input("Necessidade de enxerto ósseo (sim/não)")
        valor_vista = st.text_input("Valor total do tratamento à vista (R$)")
        data_vista = st.text_input("Data de pagamento à vista")
        valor_sinal = st.text_input("Valor do pagamento inicial (sinal)")
        data_sinal = st.text_input("Data do pagamento do sinal")
        parcelas = st.text_input("Número de parcelas restantes")
        valor_parcela = st.text_input("Valor de cada parcela (R$)")
        vencimento_parcelas = st.text_input("Dia de vencimento de cada parcela")
        multa_mora = st.text_input("Percentual de multa por atraso (%)")
        juros = st.text_input("Percentual de juros ao mês em caso de atraso (%)")
        resto_pagamento = st.text_input("Descreva como o pagamento será dividido")

        contract_text = f"""


        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:\n\n
I – Fase de Orientação:\n
O paciente será, nesta fase, orientado a respeito do que são implantes ósseo-integrados e os diversos tipos de enxertos ósseos que podem se fazer necessários em algum momento do tratamento, das suas diversas técnicas, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente. Nesta fase o paciente tomará ciência de que a ósseo-integração é dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente, não havendo outra garantia da sua ocorrência, além da probabilidade estatística.\n
Parágrafo único – O paciente ficará esclarecido e ciente de que existem fatores clínicos e que são necessários exames de imagem de última geração, mas que a odontologia é uma ciência inexata, e que podem se fazer necessários outros tipos de intervenções no tratamento, que em caso de necessidade serão negociadas à parte.\n\n
II – Fase de Planejamento:\n
Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.\n
Parágrafo único: Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento.\n\n
III – Fase cirúrgica:\n
IMPLANTE DENTE N°36.\n
Necessidade de enxerto?_______________ {enxerto} ______________________.\n\n
IV – Fase protética:\n
Esta fase será assim dividida:\n
Prótese cirúrgica: a critério do cirurgião dentista e baseado nas características de cada caso, poderá ser confeccionada uma prótese provisória, aqui considerada cirúrgica, que tem a finalidade de proteção dos implantes, não devolvendo ao paciente estética ou função.\n
Parágrafo único: a critério do cirurgião a prótese cirúrgica poderá ser a própria do paciente devidamente adaptada, se em perfeita condição para o caso.\n\n
V – Fase de preservação:\n
A fase de preservação se inicia após a terceira consulta pós-operatória, e terá a duração de 4 (quatro) ou 6 (meses), podendo ocorrer consultas mensalmente, quando necessário, e em seguida, será marcada a cirurgia de exposição dos implantes onde será constatada ou não a ósseo-integração dos mesmos.\n
Parágrafo 1º - Na fase de preservação o paciente será orientado sobre a escovação e higiene dos implantes e dos cuidados que deverá tomar para sua preservação.\n
Parágrafo 2º - A fase de preservação é obrigatória, sendo que, a falta do paciente às consultas marcadas prejudicará definitivamente o prognóstico dos implantes.\n
Parágrafo 3º - Em caso de não ocorrer a ósseo-integração o cirurgião compromete-se a recolocar outro implante, quando as condições do tecido ósseo permitirem, cabendo ao paciente apenas o pagamento do novo implante e do material. O paciente está ciente de que a ósseo-integração é um fenômeno dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente.\n
Parágrafo 4º - O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento e a permanecer sem o uso da prótese se necessário.\n
Parágrafo 5º - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião, ou por sua ausência nas consultas marcadas, o cirurgião ficará isento de responsabilidade sobre os implantes colocados. Nestes casos, a recolocação do implante ficará a critério do cirurgião dentista.\n
Parágrafo 6º - O paciente fica consciente de que, em alguns casos, não será possível a recolocação de implantes, sendo neste caso proposto outro tipo de tratamento.\n\n
VI – Do pagamento:\n
A remuneração pecuniária do tratamento ora proposto, será da seguinte maneira:\n
À vista: R$ {valor_vista} data {data_vista}\n
À prazo/sinal: R$ {valor_sinal} data {data_sinal} e o restante em {parcelas} parcelas no valor de {valor_parcela} com vencimento nos dias {vencimento_parcelas}. Peculiaridades em relação ao meio de pagamento: {resto_pagamento} \n
Parágrafo 1º - O paciente concorda que os pagamentos vencidos e efetuados fora dos prazos previstos anteriormente estarão sujeitos a multa de mora {multa_mora} % e juros de {juros} % ao mês.\n
Parágrafo 1º - O paciente concorda que os pagamentos vencidos e efetuados fora dos prazos previstos anteriormente estarão sujeitos a multa de mora {multa_mora}% e juros de {juros}% ao mês.\n
Parágrafo 2º - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o(a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.\n\n
VII – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10% a qual o paciente está ciente e de acordo com a mesma. Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.\n\n
VIII – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n\n
IX – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n\n
X – Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.\n
Parágrafo 1° – Fica acordado que o CONTRATANTE poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
Parágrafo 2° – O CONTRATANTE irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter início.\n
Parágrafo 3° – Em caso de mais de 1 (um) procedimento, caberá ao CONTRATADO realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do CONTRATANTE.\n\n
X – A responsabilidade do cirurgião dentista baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.\n\n
XI – O paciente, neste ato, doa todo o material de diagnóstico trazido pelo mesmo ou obtido durante o tratamento o qual passa a ser propriedade do cirurgião dentista, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica serão arquivados com o cirurgião dentista.\n\n
O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.\n\n
As partes elegem o Fórum da Comarca de Anápolis/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, por mais privilegiado for.\n

{assinaturas}


        """

    # *************************************************************************************

    #                   CONTRATO BOTOX ONEROSA

    # *************************************************************************************


    elif contract_option == "Contrato Botox":
        anestesia = st.text_input("Qual tipo de anestesia será usada?")
        regiao_anestesia = st.text_input("Região onde será aplicada a anestesia:")
        valor_vista = st.text_input("Valor total para pagamento à vista (R$)")
        data_vista = st.text_input("Data para o pagamento à vista")
        valor_sinal = st.text_input("Valor do sinal (entrada)")
        data_sinal = st.text_input("Data para o pagamento do sinal")
        parcelas = st.text_input("Número de parcelas restantes")
        valor_parcela = st.text_input("Valor de cada parcela (R$)")
        vencimento_parcelas = st.text_input("Dia de vencimento das parcelas")
        multa_mora = st.text_input("Percentual de multa por atraso (%)")
        juros = st.text_input("Taxa de juros ao mês para atraso (%)")
        resto_pagamento = st.text_input("Detalhes sobre a divisão dos pagamentos")

        contract_text = f"""


        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:\n\n
I – Fase de Orientação:\n
O paciente será, nesta fase, orientado a respeito do que é a aplicação de botox® (toxina botulínica), das suas diversas técnicas, do tratamento, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente. Nesta fase o paciente tomará ciência dos possíveis sintomas pós procedimento. Será informado também sobre o tratamento necessário após a realização da cirurgia e os motivos pelos quais será adotado o tratamento proposto.\n
Parágrafo único – O paciente ficará esclarecido e ciente de que a natureza deste tratamento objetiva a aplicação de BOTOX na face e possui natureza estética, com obrigação de meio e de resultado, dependendo do caso.\n\n
II – Fase de Planejamento:\n
Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.\n
Parágrafo único: Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento.\n\n
III – Fase cirúrgica:\n
Anestesia {anestesia} aplicação de BOTOX na região {regiao_anestesia}.\n\n
IV - Tratamento:\n
O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento.\n
Parágrafo único - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião e pela clínica, ou por sua ausência nas consultas marcadas, o cirurgião e a clínica ficarão isentos de responsabilidade sobre este tratamento. Existe a possibilidade de infeccionar e formar um abscesso no local da cirurgia, caso não sejam cumpridas as consultas marcadas e orientações do dentista.\n\n
V - Dos “Retoques”:\n
É sabido, pelo paciente, que procedimentos cirúrgicos posteriores ao serviço realizado (ditos “retoques”) podem ser necessários. Em qualquer tipo de cirurgia este fato é bastante comum. Daí, custos de anestesia, internação (gastos com clínica ou hospital) e, se necessário, dentista auxiliar e instrumentadora serão debitados ao paciente, não havendo, entretanto, cobrança de honorários pela Clínica.\n
Parágrafo Primeiro - Não será considerado retoque as consequências de não cuidados da paciente em relação ao pós-operatório.\n
Parágrafo Segundo - No caso de qualquer reação que seja necessário a retirada do produto, as despesas relativas a tais procedimentos serão debitadas do paciente, assim como a sua posterior colocação e compra de novos produtos.\n
Parágrafo Terceiro - É de responsabilidade do paciente informar com antecedência sobre tabagismo, uso de drogas ilícitas, uso de medicamentos como Roacutan, antidepressivos, anticoagulantes, ou quaisquer outros de uso contínuo.\n
Parágrafo Quarto - Não há aplicação de pontos extras (retoques) em botox® (toxina botulínica). Novos pontos de aplicação que venham a ser necessários serão cobrados.\n
Parágrafo Quinto - Não há retoque de aplicação em função da resposta particular de cada organismo à aplicação, podendo ser reabsorvido completamente. O valor é cobrado por aplicação. Caso o paciente queira nova aplicação será cobrado valor integral.\n
Parágrafo Sexto - Não há retoque para preenchimentos. O valor cobrado corresponde à aplicação do produto, e o volume a ser aplicado em uma sessão nem sempre é suficiente para corrigir as rugas e depressões que o paciente anseia, desta forma mais produto é necessário e o procedimento integral será cobrado.\n\n
VI - Do pagamento:\n
A remuneração pecuniária do tratamento ora proposto será da seguinte maneira:\n
À vista: R$ {valor_vista} data {data_vista}\n
À prazo/sinal: R$ {valor_sinal} data {data_sinal} e o restante em {parcelas} parcelas no valor de {valor_parcela} com vencimento nos dias {vencimento_parcelas}. Peculiaridades em relação ao meio de pagamento: {resto_pagamento} \n
Parágrafo 1º - O paciente concorda que os pagamentos vencidos e efetuados fora dos prazos previstos anteriormente estarão sujeitos a multa de mora {multa_mora} % e juros de {juros} % ao mês.\n
Parágrafo segundo - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o(a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.\n\n
VII – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10%, a qual o paciente está ciente e de acordo com a mesma. Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.\n\n
VIII – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já tiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n\n
IX – A responsabilidade do cirurgião dentista e da clínica baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.\n\n
X – O paciente, neste ato, doa todo o material de diagnóstico e planejamento (radiografias, modelos, slides, exames complementares) trazido pelo mesmo ou obtido durante o tratamento, o qual passa a ser propriedade e documento da clínica, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica, serão arquivados com a clínica.\n\n
XI – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n\n
XII – Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.\n
Parágrafo primeiro – Fica acordado que o contratante poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
Parágrafo segundo – O contratante irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter início.\n
Parágrafo terceiro – Em caso de mais de 1 (um) procedimento, caberá à contratada realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do contratante.\n\n
XII – Em relação aos dados pessoais, a clínica se compromete a cumprir o quanto exigido pela LEI GERAL DE PROTEÇÃO DE DADOS (LGPD) – Lei nº 13.709/2018, conforme abaixo.\n
Parágrafo primeiro – O paciente neste ato dá seu consentimento e autoriza a coleta de dados pessoais imprescindíveis à execução deste contrato, tendo sido informado quanto ao tratamento de dados que será realizado pela clínica, nos termos da Lei n° 13.709/2018, especificamente quanto à coleta dos seguintes dados:\n
a) Dados relacionados à sua identificação pessoal e de seus dependentes, como nome completo, RG, CPF, dentre outros dados básicos, a fim de que se garanta a fiel contratação pelo respectivo paciente;\n
b) Dados relacionados ao endereço, telefone e e-mail do paciente para eventual necessidade de utilização da clínica para envio de documentos, notificações, boletos, carnês, renovação de contrato e outras garantias necessárias ao fiel cumprimento deste instrumento;\n
c) Dados descritos nos itens a) e b) acima de crianças e adolescentes, menores de 18 (dezoito) anos, quando estes fizerem parte do presente contrato. Neste ato, o pai ou responsável legal consente especificamente e autoriza a coleta de tais dados do(s) menor(es).\n
Parágrafo segundo - Os dados coletados poderão ser utilizados para compartilhamento com a Franqueadora da marca Odontocompany; compartilhamento para órgãos de segurança, conforme solicitação legal pertinente; compartilhamento com autoridade administrativa e judicial no âmbito de suas competências com base no estrito cumprimento do dever legal; bem como com os órgãos de proteção ao crédito e empresa de cobrança, a fim de garantir a adimplência paciente.\n
Parágrafo terceiro - Os dados coletados com base no legítimo interesse do paciente, bem como para garantir a fiel execução do contrato por parte da clínica, fundamentam-se no artigo 7º da Lei 13.709/2018, razão pela qual as finalidades descritas nesta cláusula não são exaustivas.\n
Parágrafo quarto - A clínica informa que todos os dados pessoais solicitados e coletados são os estritamente necessários para os fins almejados neste contrato.\n
Parágrafo quinto – O paciente autoriza o compartilhamento de seus dados, para os fins descritos nesta cláusula, com terceiros legalmente legítimos para defender os interesses da clínica bem como do paciente.\n
Parágrafo sexto – O paciente possui o tempo determinado de 05 (cinco) anos para acesso aos próprios dados armazenados, podendo também solicitar a exclusão de dados que foram previamente coletados com seu consentimento.\n
Parágrafo sétimo - A exclusão de dados será efetuada sem que haja prejuízo por parte da clínica, tendo em vista a necessidade de guarda de documentos pelo prazo mínimo determinado de 05 (cinco) anos, conforme lei civil, consumerista, e Código de Ética Odontológico. Caso o paciente deseje efetuar a revogação de algum dado, deverá preencher uma declaração nesse sentido, ciente que a revogação de determinados dados poderá importar em eventuais prejuízos na prestação de serviços.\n
Parágrafo oitavo – O paciente autoriza, neste mesmo ato, a guarda dos documentos (contratos, notas promissórias, documentos fiscais, notificações, orçamentos) - em que pese eles possuam dados pessoais - por parte da clínica a fim de que ela cumpra com o determinado nas demais normas que regulam o presente contrato, bem como para o cumprimento da obrigação legal nos termos do artigo 16, inciso I, da Lei 13.709/2018.\n
Parágrafo nono - Em eventual vazamento indevido de dados a clínica se compromete a comunicar o paciente sobre o ocorrido, bem como sobre qual o dado vertido.\n
Parágrafo décimo - A clínica informa que a gerência de dados e a manutenção do registro das operações de tratamento de dados pessoais, ocorrerão através de um sistema que colherá e tratará os dados na forma da lei.\n
Parágrafo décimo primeiro - Em atendimento ao artigo 9º da Lei 13.709/2018, a clínica informa que sua identificação e contato telefônico, constam no primeiro parágrafo do presente instrumento.\n
Parágrafo décimo segundo: O paciente fica ciente que o tratamento de seus dados pessoais é condição para o fornecimento dos serviços ora adquiridos e terá direito a obter da clínica, em relação aos seus dados pessoais por esta tratados, a qualquer momento e mediante requisição: I - confirmação da existência de tratamento de dados; II - acesso aos seus dados; III - correção de seus dados incompletos, inexatos ou desatualizados; IV - anonimização, bloqueio ou eliminação de dados desnecessários, excessivos ou tratados em desconformidade com o disposto na Lei 13.709/2018; V - portabilidade de seus dados a outro fornecedor de serviço, mediante requisição expressa e observados os segredos comercial e industrial, de acordo com a regulamentação do órgão controlador; VI - eliminação dos dados pessoais tratados com o seu consentimento, exceto nas hipóteses previstas no art. 16 da Lei 13.709/2018.\n\n
XIII – Em relação aos dados sensíveis, a clínica se compromete a cumprir o quanto exigido pela LEI GERAL DE PROTEÇÃO DE DADOS (LGPD) – Lei nº 13.709/2018, conforme abaixo.\n
Parágrafo primeiro - Dado pessoal sensível é todo dado que diz respeito sobre origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou a organização de caráter religioso, filosófico ou político, dado referente à saúde ou à vida sexual, dado genético ou biométrico, quando vinculado a uma pessoa natural. No caso do presente contrato, uma vez que a clínica se trata de estabelecimento de saúde, precisará de dados relacionados à saúde do paciente.\n
Parágrafo segundo - Nos termos do artigo 11, inciso II, alínea “f)” da Lei 13.709/2018, não há necessidade de consentimento do paciente acerca de seus dados sensíveis, uma vez que tais dados são indispensáveis para a tutela de sua saúde, prestada por profissionais de saúde da clínica.\n\n
XIV- Rescindido o contrato, os dados pessoais e sensíveis coletados serão armazenados pelo tempo determinado na cláusula VIII, Parágrafo Sétimo. Passado o tempo de guarda pertinente, a clínica efetuará o descarte dos dados adequadamente, autorizada a conservação dos dados pelo paciente, para cumprimento de obrigação legal, perante o Código de Ética Odontológico; para uso exclusivo da clínica, com anonimação dos dados; para estudo por órgão de pesquisa; ou para outra hipótese prevista no artigo 16 da Lei 13.709/2018.\n\n
O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.\n\n
As partes elegem o Foro da Comarca de Anápolis/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, ainda que mais favorável for.\n

{assinaturas}


        """

    # *************************************************************************************

    #                   CONTRATO CANAL ONEROSA

    # *************************************************************************************


    elif contract_option == "Contrato Canal":
        valor_vista = st.text_input("Valor do pagamento à vista (R$)")
        data_vista = st.text_input("Data do pagamento à vista")
        valor_sinal = st.text_input("Valor do sinal (entrada)")
        data_sinal = st.text_input("Data para o pagamento do sinal")
        parcelas = st.text_input("Número de parcelas")
        valor_parcela = st.text_input("Valor de cada parcela (R$)")
        vencimento_parcelas = st.text_input("Dia de vencimento das parcelas")
        multa_mora = st.text_input("Percentual de multa por atraso (%)")
        juros = st.text_input("Taxa de juros ao mês para atraso (%)")
        resto_pagamento = st.text_input("Especificar como será dividido o pagamento")

        contract_text = f"""


        CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO\n

Nome do Manifestante (CONTRATANTE): {user_data['name']}\n

CPF: {user_data['cpf']}\n

CEP: {user_data['cep']}\n

Endereço: {user_data['address']}\n

{info_clinica}\n\n

Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:\n\n

I – Fase de Orientação:\n
O paciente será, nesta fase, orientado a respeito do que é o tratamento de endodontia, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente. Nesta fase o paciente tomará ciência dos possíveis sintomas pós-procedimento. Será informado também sobre o tratamento necessário após a realização da endodontia e os motivos pelos quais será adotado o tratamento proposto.\n\n

II – Fase de Planejamento:\n
Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.\n
Parágrafo único: Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento.\n\n

III – Tratamento:\n
O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento.\n
Parágrafo único - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião, ou por sua ausência nas consultas marcadas, o cirurgião ficará isento de responsabilidade sobre este tratamento. Existe a possibilidade de infeccionar, formar um abscesso e até a perda do dente, caso não sejam cumpridas as consultas marcadas e orientações do dentista.\n\n

IV - Do pagamento:\n
A remuneração pecuniária do tratamento ora proposto será da seguinte maneira:\n
À vista: R$ {valor_vista} data {data_vista}\n
À prazo/sinal: R$ {valor_sinal} data {data_sinal} e o restante em {parcelas} parcelas no valor de {valor_parcela} com vencimento nos dias {vencimento_parcelas}. Peculiaridades em relação ao meio de pagamento: {resto_pagamento} \n
Parágrafo 1º - O paciente concorda que os pagamentos vencidos e efetuados fora dos prazos previstos anteriormente estarão sujeitos a multa de mora {multa_mora} % e juros de {juros} % ao mês.\n
Parágrafo 2º - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o(a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.\n\n

V – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10%, a qual o paciente está ciente e de acordo com a mesma. Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.\n\n

VI – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já tiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.\n\n

VII – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.\n\n

VIII - Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.\n\n

Parágrafo primeiro – Fica acordado que o CONTRATANTE poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.\n
Parágrafo segundo – O CONTRATANTE irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter início.\n
Parágrafo terceiro – Em caso de mais de 1 (um) procedimento, caberá ao CONTRATADO realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária, utilizando os conhecimentos técnicos específicos na área e a necessidade do CONTRATANTE.\n\n

VIII – A responsabilidade do cirurgião dentista baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.\n\n

IX – O paciente, neste ato, doa todo o material de diagnóstico e planejamento (radiografias, modelos, slides, exames complementares) trazido pelo mesmo ou obtido durante o tratamento, o qual passa a ser propriedade e documento do cirurgião dentista, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica, serão arquivados com o cirurgião dentista.\n\n

O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.\n\n

As partes elegem o Fórum da Comarca de ARAGOIANIA/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, ainda que mais favorável for.\n
{assinaturas}


        """

    # *************************************************************************************

    #                   último contrato

    # *************************************************************************************


    else:
        # Texto do contrato "Não Quero Sorvete"
        contract_text = f"""
        ESCOLHA UM CONTRATO
        """


     # *************************************************************************************

    #                   FIM DOS CONTRATOS

    # *************************************************************************************




    # Pré-visualização e download do PDF
    if contract_text:
        st.subheader("Pré-visualização do Contrato")
        st.text_area("Contrato", contract_text, height=200)

        pdf_data = generate_pdf(contract_text, logo_image=user_data["logo"])
        
        file_name = f"contrato_{user_data['name']}.pdf"
        st.download_button(
            label="Baixar contrato em PDF",
            data=pdf_data,
            file_name=file_name,
            mime="application/pdf"
        )
    else:
        st.write("Por favor, selecione o tipo de contrato e preencha as informações para gerar o PDF.")
else:
    st.write("Por favor, carregue um documento PDF para extrair as informações.")


# cd C:\Users\tomas\OneDrive\Área de Trabalho\ContratoPDF && ambienteVirtual\Scripts\activate && streamlit run pagina.py
