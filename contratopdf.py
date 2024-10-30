from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import streamlit as st
from PyPDF2 import PdfReader
import re
import tempfile
from PIL import Image

def extract_info_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    full_text = ""
    
    for page in pdf_reader.pages:
        full_text += page.extract_text()
    
    name_pattern = r"NOME.....: \s?([\s\S]+?)\s?ENDERECO.: "
    cpf_pattern = r"CNPJ/CPF.:\s?(\d{3}\.?\d{3}\.?\d{3}-?\d{2})"
    cep_pattern = r"CEP......:\s?(\d{5}-\d{3})"
    address_pattern = r"ENDERECO.: \s?([\s\S]+?)\s?BAIRRO...: "

    name_match = re.search(name_pattern, full_text)
    cpf_match = re.search(cpf_pattern, full_text)
    cep_match = re.search(cep_pattern, full_text)
    address_match = re.search(address_pattern, full_text)  # Corrigido: adiciona 'full_text' como segundo argumento
    
    name = name_match.group(1) if name_match else "Nome não encontrado no documento."
    cpf = cpf_match.group(1) if cpf_match else "CPF não encontrado no documento."
    cep = cep_match.group(1) if cep_match else "CEP não encontrado no documento."
    
    if address_match:
        address = " ".join(address_match.group(1).split())
    else:
        address = "Endereço não encontrado no documento."
    
    return name, cpf, cep, address

def generate_pdf(content, logo_image=None):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4
    margin_x = 50
    top_margin_y = height - 50
    bottom_margin_y = 50
    max_text_width = width - 2 * margin_x
    line_spacing = 15
    page_number = 1

    if logo_image:
        logo_img = Image.open(logo_image)
        logo_width, logo_height = logo_img.size
        max_logo_width = width * 0.33
        scaling_factor = max_logo_width / logo_width
        logo_display_width = logo_width * scaling_factor
        logo_display_height = logo_height * scaling_factor
        logo_x_position = (width - logo_display_width) / 2
        logo_y_position = height - logo_display_height - 20
        c.drawImage(logo_image, logo_x_position, logo_y_position, 
                    width=logo_display_width, height=logo_display_height)
        top_margin_y -= logo_display_height + 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, top_margin_y, "Contrato")
    top_margin_y -= 30
    
    c.setFont("Helvetica", 12)
    text = c.beginText(margin_x, top_margin_y)
    text.setLeading(line_spacing)
    
    paragraphs = content.splitlines()
    available_height = top_margin_y - bottom_margin_y
    lines_per_page = int(available_height / line_spacing)
    
    line_count = 0
    for paragraph in paragraphs:
        if not paragraph.strip():
            line_count += 1
            if line_count >= lines_per_page:
                c.drawText(text)
                c.setFont("Helvetica", 8)
                c.drawRightString(width - margin_x, bottom_margin_y, f"Contrato termo de consentimento - Página {page_number}")
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
                        c.drawRightString(width - margin_x, bottom_margin_y, f"Contrato termo de consentimento - Página {page_number}")
                        c.showPage()
                        page_number += 1
                        text = c.beginText(margin_x, height - 50)
                        line_count = 0
            text.textLine(line.strip())
            line_count += 1

    c.drawText(text)
    c.setFont("Helvetica", 8)
    c.drawRightString(width - margin_x, bottom_margin_y, f"Contrato termo de consentimento - Página {page_number}")
    c.showPage()
    c.save()
    
    pdf_buffer.seek(0)
    return pdf_buffer

st.title("App Geração de Contrato")

uploaded_pdf = st.file_uploader("Faça o upload do documento PDF", type="pdf")

if "confirmed_data" not in st.session_state:
    st.session_state["confirmed_data"] = None

if uploaded_pdf is not None and st.session_state["confirmed_data"] is None:
    name, cpf, cep, address = extract_info_from_pdf(uploaded_pdf)
    
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

if st.session_state["confirmed_data"] is not None:
    user_data = st.session_state["confirmed_data"]
    st.write("**Informações confirmadas:**")
    st.write(f"**Nome:** {user_data['name']}")
    st.write(f"**CPF:** {user_data['cpf']}")
    st.write(f"**CEP:** {user_data['cep']}")
    st.write(f"**Endereço:** {user_data['address']}")
    
    st.subheader("Escolha o tipo de contrato")
    contract_option = st.selectbox("Selecione o contrato", ["Contrato de Enxerto Ósseo", "Contrato Não Quero Sorvete"])
    
    food_choice = st.text_input("Digite a comida que deseja ou não deseja")
    
    if contract_option == "Contrato de Enxerto Ósseo":
        dente = st.text_input("Digite qual será o dente escolhido")
        
        payment_option = st.selectbox("Escolha a forma de pagamento", ["À vista", "Parcelado"])
        
        if payment_option == "À vista":
            valor_total = st.text_input("Valor total à vista (R$)")
            data_vista = st.text_input("Data para pagamento à vista")
            contract_text = f"""
            CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO

            Nome do Paciente (CONTRATANTE): {user_data['name']}
            CPF: {user_data['cpf']}
            CEP: {user_data['cep']}
            Endereço: {user_data['address']}

            Nome da Clínica (CONTRATADA): ODONTOCOMPANY
            Unidade: ABADIA DE GOIÁS
            Endereço: AV COMERCIAL, QD 6 LT 5. CENTRO. 75345-959
            Cirurgião Dentista Responsável: Mariana Silva Xavier
            CRO/GO: 17928 \n
            \n
            
        
            Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:

            I – Fase de Orientação: O paciente será, nesta fase, orientado a respeito do que são enxertos, das suas diversas técnicas, do tratamento, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente. Nesta fase o paciente tomará ciência de que a integração e cicatrização do enxerto é dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente, não havendo outra garantia da sua ocorrência, além da probabilidade estatística.

            Parágrafo único – O paciente ficará esclarecido e ciente de que a natureza deste tratamento objetiva a recuperação óssea e que estética não será o objetivo do mesmo.

            II – Fase de Planejamento: Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.
Parágrafo único: Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento. 

            III – Fase cirúrgica: Colocação de enxerto ósseo assim distribuídos na região do(s) dente(s)_____________{dente}________________________________.

            IV – Fase de preservação: A fase de preservação terá a seguinte duração:
No primeiro mês: uma consulta semanal ou mensal, dependendo do caso.
Nos 3 (três) meses seguintes: uma consulta mensal
Parágrafo 1º - Na fase de preservação o paciente será orientado sobre a escovação e higiene e dos cuidados que deverá tomar para a preservação do enxerto.
Parágrafo 2º - A fase de preservação é obrigatória, sendo que, a falta do paciente às consultas marcadas prejudicará definitivamente o prognóstico do enxerto.
Parágrafo 3º - Em caso de não ocorrer a cicatrização e integração o cirurgião compromete-se a recolocar outro enxerto, quando as condições do tecido ósseo permitirem, cabendo ao paciente apenas o pagamento do novo enxerto e do material. O paciente está ciente de que a cicatrização e integração do enxerto é um fenômeno dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente.
Parágrafo 4º - O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento e a permanecer sem o uso da prótese se necessário.
Parágrafo 5º - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião, ou por sua ausência as consultas marcadas, o cirurgião ficará isento de responsabilidade sobre o enxerto ósseo colocado. Nestes casos, a recolocação do enxerto ficará a critério do cirurgião dentista.
Parágrafo 6º - O paciente fica consciente de que, em alguns casos, não será possível a recolocação do enxerto ósseo sendo neste caso proposto outro tipo de tratamento.

            V – Do pagamento: a remuneração pecuniária do tratamento ora proposto, será da seguinte maneira:
            - À vista: R$ {valor_total} - Data: {data_vista}

            Parágrafo 2º - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o (a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.

            VI – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10% a qual o paciente está ciente e de acordo com a mesma.  Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.

            VII – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.

            VIII – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.

            VIII - Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.

            Parágrafo 1° – Fica acordado que o CONTRATANTE poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.

            Parágrafo 2° – O CONTRATANTE irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter inicio.

            Parágrafo 3° – Em caso de mais de 1 (um) procedimento, caberá ao CONTRATADO realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do CONTRATANTE

            IX– A responsabilidade do cirurgião dentista baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.

            X – O paciente, neste ato, doa todo o material de diagnóstico e planejamento (radiografias, modelos, slides, exames complementares) trazido pelo mesmo ou obtido durante o tratamento o qual passa a ser propriedade e documento do cirurgião dentista, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica serão arquivados com o cirurgião dentista.

            O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.

            As partes elegem o Fórum da Comarca de Anápolis/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, ainda que mais favorável for.

            DATA: ____________/______________/_____________

            CIDADE:_____________________________________________

            _____________________________		              ____________________________
             Paciente (CONTRATANTE)                                 CLÍNICA (CONTRATADO)


            _____________________________		              ____________________________
                    Testemunha 1					              Testemunha 2
            """
        else:
            valor_parcelado = st.text_input("Valor parcelado (R$)")
            data_entrada = st.text_input("Data da entrada")
            parcelas = st.text_input("Número de parcelas")
            valor_parcela = st.text_input("Valor de cada parcela (R$)")
            vencimento_parcelas = st.text_input("Vencimento das parcelas")
            multa_mora = st.text_input("Multa de mora (%)")
            juros = st.text_input("Juros ao mês (%)")

            contract_text = f"""

            CONTRATO DE PRESTAÇÃO DE SERVIÇOS ODONTOLÓGICOS – ENXERTO ÓSSEO

            Nome do Paciente (CONTRATANTE): {user_data['name']}
            CPF: {user_data['cpf']}
            CEP: {user_data['cep']}
            Endereço: {user_data['address']}

            Nome da Clínica (CONTRATADA): ODONTOCOMPANY
            Unidade: ABADIA DE GOIÁS
            Endereço: AV COMERCIAL, QD 6 LT 5. CENTRO. 75345-959
            Cirurgião Dentista Responsável: Mariana Silva Xavier
            CRO/GO: 17928 \n
            \n
            
        
            Pelo presente contrato particular, o usuário a seguir signatário e qualificado acima, adiante denominado PACIENTE ou RESPONSÁVEL, vem contratar a prestação de serviços odontológicos da clínica também acima qualificada, neste ato denominada como CONTRATADA, estando ciente de que as particularidades de tratamento reger-se-ão mediante as seguintes condições:

            I – Fase de Orientação: O paciente será, nesta fase, orientado a respeito do que são enxertos, das suas diversas técnicas, do tratamento, através de literatura, fotos, modelos e radiografias, bem como dos seus direitos e deveres como paciente. Nesta fase o paciente tomará ciência de que a integração e cicatrização do enxerto é dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente, não havendo outra garantia da sua ocorrência, além da probabilidade estatística.

            Parágrafo único – O paciente ficará esclarecido e ciente de que a natureza deste tratamento objetiva a recuperação óssea e que estética não será o objetivo do mesmo.

            II – Fase de Planejamento: Nesta fase, o profissional odontólogo realizará todo o planejamento do tratamento do paciente, discernindo todas as técnicas que serão aplicadas no caso concreto, e todas as fases em que o paciente irá ser submetido, avaliando a complexidade de cada tratamento, dando uma estimativa do que irá ser realizado em cada consulta profissional.
Parágrafo único: Esta fase ocorre após o pagamento da primeira parcela/entrada, e envolve nítido esforço intelectual e tempo do profissional odontólogo, que preparará todas as fases do tratamento mediante avaliação, e irá organizar todos os preparativos para um tratamento efetivo e resolutivo, que corresponderá a porcentagem de 15% do valor do tratamento. 

            III – Fase cirúrgica: Colocação de enxerto ósseo assim distribuídos na região do(s) dente(s)_____________{dente}________________________________.

            IV – Fase de preservação: A fase de preservação terá a seguinte duração:
No primeiro mês: uma consulta semanal ou mensal, dependendo do caso.
Nos 3 (três) meses seguintes: uma consulta mensal
Parágrafo 1º - Na fase de preservação o paciente será orientado sobre a escovação e higiene e dos cuidados que deverá tomar para a preservação do enxerto.
Parágrafo 2º - A fase de preservação é obrigatória, sendo que, a falta do paciente às consultas marcadas prejudicará definitivamente o prognóstico do enxerto.
Parágrafo 3º - Em caso de não ocorrer a cicatrização e integração o cirurgião compromete-se a recolocar outro enxerto, quando as condições do tecido ósseo permitirem, cabendo ao paciente apenas o pagamento do novo enxerto e do material. O paciente está ciente de que a cicatrização e integração do enxerto é um fenômeno dependente de múltiplos fatores que podem independer do controle do cirurgião ou do paciente.
Parágrafo 4º - O paciente compromete-se a comparecer às consultas marcadas, quantas forem, e a executar os exames solicitados para o bom andamento do tratamento e a permanecer sem o uso da prótese se necessário.
Parágrafo 5º - Em caso de insucesso motivado pelo não cumprimento, por parte do paciente, das orientações dadas pelo cirurgião, ou por sua ausência as consultas marcadas, o cirurgião ficará isento de responsabilidade sobre o enxerto ósseo colocado. Nestes casos, a recolocação do enxerto ficará a critério do cirurgião dentista.
Parágrafo 6º - O paciente fica consciente de que, em alguns casos, não será possível a recolocação do enxerto ósseo sendo neste caso proposto outro tipo de tratamento.

            V – Do pagamento:
            - Parcelado: R$ {valor_parcelado} (entrada de R$ {data_entrada}) e {parcelas} parcelas de R$ {valor_parcela} com vencimento em {vencimento_parcelas}.
            Em caso de atraso, será aplicada uma multa de mora de {multa_mora}% sobre o valor da parcela, acrescida de juros de {juros}% ao mês.

            Parágrafo 2º - Em caso de medida judicial por inadimplência dos pagamentos supracitados, o (a) paciente se obriga ao pagamento de honorários advocatícios, acrescidos de custas e despesas processuais.

            VI – Em caso de desistência por parte do paciente, o cirurgião resguarda o direito do ressarcimento das despesas de material e contratação de terceiros decorrentes do mesmo, até a data da desistência, além de uma multa rescisória de 10% a qual o paciente está ciente e de acordo com a mesma.  Será considerada desistência a falta em duas consultas consecutivas ou ausência maior de trinta dias sem aviso por escrito de parte do paciente.

            VII – Se houver a desistência, a fase de planejamento correspondente a 15% (quinze por cento) do valor do contrato não será reembolsada, se já estiver sido concluída, tendo em vista que o profissional já terá realizado todo o trabalho acordado entre as partes e o tratamento do cliente já estará devidamente planejado.

            VIII – Fica acordado entre as partes que a realização do tratamento irá ficar condicionada ao pagamento do valor integral de cada procedimento almejado, de acordo com a tabela da OdontoCompany vigente à época da assinatura do contrato, e não ao pagamento das parcelas.

            VIII - Em caso de desistência por parte do paciente, fica definido o prazo de até 15 dias úteis para a devolução do valor a ser ressarcido do tratamento já pago.

            Parágrafo 1° – Fica acordado que o CONTRATANTE poderá realizar o adiantamento das parcelas para que o tratamento seja realizado de forma mais célere/adiantado.

            Parágrafo 2° – O CONTRATANTE irá realizar o pagamento das parcelas até que estas completem o valor do procedimento almejado, e só após completar o valor do procedimento o tratamento poderá ter inicio.

            Parágrafo 3° – Em caso de mais de 1 (um) procedimento, caberá ao CONTRATADO realizar a divisão de valores do contrato para a obtenção ao direito à realização de cada procedimento e quais procedimentos serão realizados de forma primária utilizando os conhecimentos técnicos específicos na área e a necessidade do CONTRATANTE

            IX– A responsabilidade do cirurgião dentista baseia-se nas regras do Código de Ética Odontológica e dos preceitos e conceitos publicados na literatura odontológica brasileira.

            X – O paciente, neste ato, doa todo o material de diagnóstico e planejamento (radiografias, modelos, slides, exames complementares) trazido pelo mesmo ou obtido durante o tratamento o qual passa a ser propriedade e documento do cirurgião dentista, sendo que no final do tratamento, ou em caso de desistência ou impossibilidade técnica serão arquivados com o cirurgião dentista.

            O paciente declara que todas as suas dúvidas a respeito do tratamento proposto foram sanadas satisfatoriamente, estando de pleno acordo com o mesmo e assina neste ato o presente contrato do qual recebeu uma cópia de igual teor.

            As partes elegem o Fórum da Comarca de Anápolis/GO para dirimir quaisquer lides oriundas do presente contrato, renunciando expressamente a qualquer outro, ainda que mais favorável for.

            DATA: ____________/______________/_____________

            CIDADE:_____________________________________________

            _____________________________		              ____________________________
             Paciente (CONTRATANTE)                                 CLÍNICA (CONTRATADO)


            _____________________________		              ____________________________
                    Testemunha 1					              Testemunha 2
            
            """
    
    st.subheader("Pré-visualização do Contrato")
    st.text_area("Contrato", contract_text, height=200)

    uploaded_logo = st.file_uploader("Faça o upload da logo", type=["png", "jpg", "jpeg"])

    # Define logo path based on user's input or use default
    logo_image = uploaded_logo if uploaded_logo else 'C:/Users/tomas/OneDrive/Área de Trabalho/ContratoPDF/OdontoLogo.png'
    
    pdf_data = generate_pdf(contract_text, logo_image=logo_image)
    
    file_name = f"contrato_{user_data['name']}.pdf"
    st.download_button(
        label="Baixar contrato em PDF",
        data=pdf_data,
        file_name=file_name,
        mime="application/pdf"
    )
else:
    st.write("Por favor, carregue um documento PDF para extrair as informações.")


# cd C:\Users\tomas\OneDrive\Área de Trabalho\ContratoPDF && ambienteVirtual\Scripts\activate && streamlit run contratopdf.py
