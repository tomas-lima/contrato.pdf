import streamlit as st
from fpdf import FPDF
from PIL import Image

# Configuração da página para alterar o título e ícone da aba do navegador
st.set_page_config(page_title="Gerador de Contratos LOGA", page_icon="📝")

# Função para corrigir caracteres especiais
def corrigir_texto(texto):
    return (texto.replace("“", '"')
                  .replace("”", '"')
                  .replace("‘", "'")
                  .replace("’", "'")
                  .replace("–", "-")
                  .replace("—", "-"))

# Função para gerar o contrato com base nos dados
def gerar_contrato(dados, clausulas):
    contrato = f"""
    CONTRATADO: LOGA PUBLICIDADE E COMUNICAÇÃO LTDA, pessoa jurídica de direito privado, inscrita no CNPJ sob n 54.185.367/0001-56, neste ato representada por {dados['representante_contratada']}, {dados['nacionalidade_contratada']}, {dados['profissao_contratada']}, {dados['estado_civil_contratada']}, CPF {dados['cpf_contratada']}; estabelecida na {dados['endereco_contratada']}, endereço eletrônico {dados['email_contratada']}, fone: {dados['telefone_contratada']}, doravante denominada “CONTRATADA”;
    
    Por outro lado,
    
    CONTRATANTE: {dados['contratante']}, pessoa jurídica de direito privado, inscrita no CNPJ sob nº {dados['cnpj_contratante']}, neste ato representada por {dados['representante_1']}, {dados['nacionalidade_1']}, {dados['profissao_1']}, {dados['estado_civil_1']}, CPF nº {dados['cpf_1']}; estabelecida na {dados['endereco_contratante']}. CEP: {dados['cep_contratante']} endereço eletrônico {dados['email_contratante']}, telefone: {dados['telefone_contratante']}.

    Ambas juntas denominadas “AS PARTES”;

    CONSIDERANDO QUE:
    A) A CONTRATADA é uma empresa de comunicação e Marketing que oferece os serviços de: Produção de peças publicitarias, produção audiovisual, elaboração de roteiros e estratégias de marketing e tráfego pago.
    B) A CONTRATADA desenvolve e oferece várias estratégias e ferramentas das quais tem total domínio para que os clientes experimentem o poder do Marketing Digital, da boa gestão, do design e de toda a modernidade e possibilidades das últimas tecnologias e mercados digitais.
    C) Todos os serviços oferecidos são focados em resultados para que os clientes possam avaliar seus empreendimentos, empresas ou marcas através de métricas de antes e depois.

    CELEBRAM o presente instrumento particular, as partes têm, entre si, justo e acertado o presente Contrato de Prestação de Serviço para Gestão de Mídias Sociais, que se regerá pelas cláusulas seguintes e pelas condições descritas no presente contrato.

    DO OBJETO:
    CLÁUSULA 1ª: Por meio deste instrumento, A CONTRATADA, em caráter não eventual e sem vínculos de dependência, assume a obrigação de gerir, às contas da CONTRATANTE, mediante REMUNERAÇÃO MENSAL FIXA, por contrato anual, das redes sociais INSTAGRAM e FACEBOOK da CONTRATANTE.

    DAS OBRIGAÇÕES DA CONTRATADA:
    CLÁUSULA 2ª: Por força do presente instrumento e para a execução dos serviços ora contratados, constituem obrigações da CONTRATADA, além de outras definidas expressamente neste instrumento e na legislação aplicável à espécie:
    """
    
    # Inserir as cláusulas opcionais
    for clausula, incluir in clausulas.items():
        if incluir:
            contrato += f"{clausula}\n\n"
    
    contrato += f"""
    Parágrafo 1º: A CONTRATADA reconhece que, na hipótese de violação deste contrato, ou de qualquer de suas cláusulas ou condições aqui ajustadas, estará sujeita às sanções e penalidades estabelecidas na legislação brasileira.
    Parágrafo 2º: Caso as imagens criadas sejam utilizadas para fins de promoção/campanhas de marketing no FacebookAds, deverá haver concordância expressa do CONTRATANTE;
    Parágrafo 3º: A CONTRATADA compromete-se em não utilizar imagens ou vídeos indevidos, com direitos autorais reservados a terceiros, sob pena de ser responsabilizada, ainda, os artigos publicados são de autoria da CONTRATADA, sendo estes objetos de revisão e aprovação e autorização de publicação da CONTRATANTE antes de sua veiculação nas mídias previamente estabelecidas.

    DAS OBRIGAÇÕES DA CONTRATANTE:
    CLÁUSULA 3ª: Por força do presente instrumento e para a execução dos serviços ora contratados, constituem obrigações da CONTRATANTE, além de outras definidas expressamente neste instrumento e na legislação aplicável à espécie:
    A) A CONTRATANTE compromete-se ao necessário fornecimento à CONTRATADA das informações e elementos necessários ao início e ao desenvolvimento do projeto, em suporte digital, dentro de um prazo máximo de 5 dias úteis, para evitar atrasos ou interrupções do serviço.
    B) Efetuar o pagamento dos valores devidos à CONTRATADA dentro dos limites e prazos estabelecidos.

    DO PAGAMENTO:
    CLÁUSULA 9ª: O presente instrumento tem valor total de R$ {dados['valor_total']} ({dados['valor_extenso_total']}), que deverão ser pagos da seguinte maneira:
    Entrada: R$ {dados['valor_entrada']} ({dados['valor_extenso_entrada']}) via transferência bancária ou pix.
    {dados['numero_parcelas']} parcelas de R$ {dados['valor_mes']} ({dados['valor_extenso_mensal']}) em recorrência mensal.

    DA RESCISÃO:
    CLÁUSULA 11ª: O presente instrumento será rescindido por descumprimento de qualquer das partes das cláusulas previstas neste contrato.

    FORO:
    CLÁUSULA 21ª: As partes elegem o Foro de Anápolis para dirimir judicialmente as controvérsias inerentes do presente contrato.

    E, assim por estarem justos e contratados, firmam o presente instrumento, em 2 vias de igual forma e teor, na presença de 2 (duas) testemunhas, abaixo assinadas.
    """

    # Aplica a função de correção de caracteres especiais
    contrato = corrigir_texto(contrato)
    
    return contrato

# Função para gerar o PDF com margens ajustadas e centralizar a logo
def gerar_pdf(contrato_texto, logo_path=None):
    pdf = FPDF()
    pdf.set_margins(10, 10, 10)  # Define as margens: esquerda, topo, direita (10 mm de cada lado)
    pdf.add_page()
    
    # Se a logo for fornecida, centraliza ela
    if logo_path:
        # Definir tamanho da imagem
        logo_width = 60  # Largura da imagem
        page_width = pdf.w - 20  # Largura da página com margens
        x_position = (page_width - logo_width) / 2  # Calcula a posição para centralizar a imagem
        pdf.image(logo_path, x=x_position, y=10, w=logo_width)  # Adiciona a imagem na posição calculada
        pdf.ln(50)  # Pula linhas para dar espaço após a logo
    
    pdf.set_font("Arial", size=12)

    # Divide o texto do contrato em linhas e adiciona cada linha ao PDF
    for linha in contrato_texto.split('\n'):
        pdf.multi_cell(0, 10, txt=linha.encode('latin-1', 'replace').decode('latin-1'))

    # Salva o PDF gerado
    pdf_output = "contrato_gerado.pdf"
    pdf.output(pdf_output)
    return pdf_output

# Interface do Streamlit
st.title("Gerador de Contrato")

# Seção de upload para a logo
logo = st.file_uploader("Escolha a imagem para o logo (PNG, JPG)", type=["png", "jpg", "jpeg"])

# Salva a logo temporariamente se o usuário fizer upload
logo_path = None
if logo:
    image = Image.open(logo)  # Abre a imagem usando Pillow
    logo_path = "logo_temp.png"  # Define um nome temporário para salvar a logo
    image.save(logo_path)  # Salva a imagem temporária no diretório atual

# Coleta de dados para o contrato
st.header("Informações do Contrato")
dados = {}
dados['representante_contratada'] = st.text_input("Nome do Representante da Contratada")
dados['cpf_contratada'] = st.text_input("CPF do Representante")
dados['nacionalidade_contratada'] = st.text_input("Nacionalidade do Representante")
dados['profissao_contratada'] = st.text_input("Profissão do Representante")
dados['estado_civil_contratada'] = st.text_input("Estado Civil do Representante")
dados['endereco_contratada'] = st.text_input("Endereço da Contratada")
dados['email_contratada'] = st.text_input("Email da Contratada")
dados['telefone_contratada'] = st.text_input("Telefone da Contratada")

dados['contratante'] = st.text_input("Nome da Contratante")
dados['cnpj_contratante'] = st.text_input("CNPJ da Contratante")
dados['endereco_contratante'] = st.text_input("Endereço da Contratante")
dados['cep_contratante'] = st.text_input("CEP da Contratante")
dados['telefone_contratante'] = st.text_input("Telefone da Contratante")
dados['email_contratante'] = st.text_input("Email da Contratante")
dados['representante_1'] = st.text_input("Nome do 1º Representante")
dados['cpf_1'] = st.text_input("CPF do 1º Representante")
dados['nacionalidade_1'] = st.text_input("Nacionalidade do 1º Representante")
dados['profissao_1'] = st.text_input("Profissão do 1º Representante")
dados['estado_civil_1'] = st.text_input("Estado Civil do 1º Representante")

# Seção de pagamento e valores
st.header("Pagamento")
dados['valor_total'] = st.number_input("Valor Total (R$)", min_value=0.0, step=100.0)
dados['valor_extenso_total'] = st.text_input("Valor Total por Extenso")
dados['valor_entrada'] = st.number_input("Valor de Entrada (R$)", min_value=0.0, step=100.0)
dados['valor_extenso_entrada'] = st.text_input("Valor de Entrada por Extenso")
dados['numero_parcelas'] = st.number_input("Número de Parcelas", min_value=1, step=1)
dados['valor_mes'] = st.number_input("Valor por Mês (R$)", min_value=0.0, step=100.0)
dados['valor_extenso_mensal'] = st.text_input("Valor Mensal por Extenso")

# Cláusulas opcionais selecionáveis com checkboxes
st.subheader("Cláusulas Opcionais")
clausulas = {
    "Executar os serviços contratados com estrita observância dos prazos, especificações técnicas e instruções constantes deste instrumento, com a competência e diligência habituais e necessárias, visando assegurar o bom e eficaz desempenho das atividades relacionadas ao objeto deste instrumento;": st.checkbox("Incluir cláusula sobre execução de serviços"),
    "Apresentar à CONTRATANTE sempre que solicitado, informações pertinentes aos serviços objeto deste instrumento.": st.checkbox("Incluir cláusula sobre apresentação de informações"),
    "Realizar a postagem de 6 posts estáticos em feed por mês.": st.checkbox("Incluir cláusula sobre posts estáticos"),
    "Realizar a postagem de 4 vídeos com qualidade de captação e edição profissional por mês com até 30s, com gravação mensal, não cumulativa em data pré-agendada, sujeita a disponibilidade do contratante e contratada.": st.checkbox("Incluir cláusula sobre vídeos mensais"),
    "Construir mensalmente cronograma de linha editorial para story de produção diária.": st.checkbox("Incluir cláusula sobre cronograma editorial"),
    "1 Roteiro de vídeo por semana com edição simples.": st.checkbox("Incluir cláusula sobre roteiro de vídeo semanal"),
    "Gerenciar as redes sociais INSTAGRAM e FACEBOOK da contratante.": st.checkbox("Incluir cláusula sobre gestão de redes sociais"),
    "Serviço de tráfego, ao qual a receberá fee de 10% sobre o valor investido.": st.checkbox("Incluir cláusula sobre serviço de tráfego"),
    "A apresentação, para aprovação pela contratante, das referidas imagens, com antecedência mínima de 01 dias à sua respectiva publicação, cujos conteúdos e cronograma serão previamente estabelecidos em comum acordo entre as partes.": st.checkbox("Incluir cláusula sobre aprovação de imagens"),
    "Realizar o agendamento das postagens nas redes determinadas.": st.checkbox("Incluir cláusula sobre agendamento de postagens"),
    "Orientar a CONTRATANTE nas atividades que lhe couber.": st.checkbox("Incluir cláusula sobre orientação"),
    "Realizar o alinhamento de cronograma trimestral por reunião online ou presencial.": st.checkbox("Incluir cláusula sobre alinhamento de cronograma"),
    "Realizar a edição de 8 vídeos mensais em formato reels com duração de até 60 segundos, sendo 4 para o cliente 'Outside Home' e 4 para o cliente 'Arthen Empreendimentos'.": st.checkbox("Incluir cláusula sobre edição de vídeos")
}

# Botão para gerar o contrato
if st.button("Gerar Contrato"):
    contrato_gerado = gerar_contrato(dados, clausulas)  # Gera o texto do contrato com base nos dados e cláusulas
    st.subheader("Contrato Gerado:")
    st.text(contrato_gerado)  # Exibe o contrato na interface do Streamlit
    
    # Gera o PDF e inclui a logo se ela for fornecida
    pdf_file_path = gerar_pdf(contrato_gerado, logo_path)
    
    # Permite que o usuário faça o download do PDF gerado
    with open(pdf_file_path, "rb") as pdf_file:
        st.download_button(label="Baixar Contrato em PDF", data=pdf_file, file_name="contrato.pdf", mime="application/pdf")
