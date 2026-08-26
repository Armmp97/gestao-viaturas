# -*- coding: utf-8 -*-
"""
v3: Constrói o índice de pesquisa da Intranet DomusCar.
- TODOS os módulos registados no openModule() do intranet.html (v2 só tinha 19 → muitos
  módulos novos não apareciam na pesquisa).
- Palavras-chave/sinónimos por módulo (entram nos headings, com peso alto na pesquisa).
- SUB-ENTRADAS para cards/sub-páginas conhecidos (deep-link via openModule(id, subId)).

Correr na pasta DomusCar:  python _build_search_index.py   (ou Regerar_Indice_Pesquisa.bat)
Depois: upload de search-index.js para o GitHub.
"""
import re, json, html
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# id → registo. "kw": sinónimos/termos que as pessoas escrevem na pesquisa.
MODULES = {
    # ---- Empresa e Cultura / Onboarding ----
    "visao_missao":        {"title": "Visão, Missão & Valores",                 "file": "intranet_visao_missao.html",        "icon": "🎯", "section": "Empresa e Cultura",
                            "kw": "cultura empresa valores missao visao principios lideranca"},
    "estrutura_org":       {"title": "Estrutura Organizacional",                "file": "estrutura_organizacional.html",      "icon": "🏢", "section": "Empresa e Cultura",
                            "kw": "organigrama organograma equipa chefias hierarquia quem e quem contactos"},
    "normas_regras":       {"title": "Normas e Regras Internas",                "file": "normas_regras_internas.html",        "icon": "📜", "section": "Empresa e Cultura",
                            "kw": "regulamento regras horario conduta disciplina normas internas"},
    "qualidade_seguranca": {"title": "Qualidade e Segurança",                   "file": "qualidade_seguranca.html",           "icon": "🛡️", "section": "Conhecimento e Ferramentas",
                            "kw": "seguranca trabalho epi acidentes qualidade iso bosch"},
    "doc_tecnica":         {"title": "Documentação Técnica",                    "file": "documentacao_tecnica.html",          "icon": "📖", "section": "Conhecimento e Ferramentas",
                            "kw": "manuais esquemas documentacao tecnica esi tronic"},
    "sistemas_ferramentas":{"title": "Sistemas e Ferramentas",                  "file": "sistemas_ferramentas.html",          "icon": "🔧", "section": "Conhecimento e Ferramentas",
                            "kw": "software officegest 2smart sistemas ferramentas informatica"},
    "recursos_humanos":    {"title": "Recursos Humanos",                        "file": "recursos_humanos.html",              "icon": "👥", "section": "Colaborador",
                            "kw": "rh ferias faltas justificacao recibos vencimento salario formacao documentos pessoais"},
    "indicadores_obj":     {"title": "Indicadores e Objetivos",                 "file": "indicadores_objetivos.html",         "icon": "📊", "section": "Conhecimento e Ferramentas",
                            "kw": "kpi kpis margem ticket medio retencao objetivos resultados mensais"},
    "sugestoes_melhoria":  {"title": "Área de Sugestões e Melhoria",            "file": "sugestoes_melhoria.html",            "icon": "💡", "section": "Qualidade e Melhoria",
                            "kw": "sugestao melhoria ideia"},
    "caixa_sugestoes":     {"title": "Caixa de Sugestões",                      "file": "caixa_sugestoes.html",               "icon": "📝", "section": "Qualidade e Melhoria",
                            "kw": "sugestao ideia melhoria propor"},
    "formulario_nc":       {"title": "Formulário de Não-Conformidade",          "file": "formulario_nao_conformidade.html",   "icon": "⚠️", "section": "Qualidade e Melhoria",
                            "kw": "nao conformidade nc reclamacao problema ocorrencia"},
    "processos_op":        {"title": "Processos Operacionais",                  "file": "processos_operacionais.html",        "icon": "⚙️", "section": "Qualidade e Melhoria",
                            "kw": "processos leiloes peritagens teste estrada viaturas prontas procedimentos"},
    "formacao":            {"title": "Calendário de Formação",                  "file": "formacao.html",                      "icon": "🎓", "section": "Colaborador",
                            "kw": "formacao calendario cursos eventos plano formativo"},
    # ---- Operações ----
    "viaturas":            {"title": "Serviço de Mobilidade",                   "file": "gestao-viaturas.html",               "icon": "🚗", "section": "Operações",
                            "kw": "viaturas cortesia substituicao levantamento devolucao mobilidade carros emprestimo"},
    "relatorio_tecnico":   {"title": "Gerador de Relatórios Técnicos",          "file": "relatorio-tecnico.html",             "icon": "📄", "section": "Operações",
                            "kw": "relatorio tecnico peritagem diagnostico avaria fotografias"},
    "editor_valpirent":    {"title": "Editor Contrato Valpirent",               "file": "editor-contrato-valpirent.html",     "icon": "✏️", "section": "Operações",
                            "kw": "valpirent valpi rent contrato aluguer alterar precos duplicado kms assinaturas"},
    "declaracoes_presenca":{"title": "Declarações de Presença",                 "file": "declaracoes-presenca.html",          "icon": "🖨️", "section": "Operações",
                            "kw": "declaracao presenca comprovativo cliente oficina imprimir"},
    "registo_horas":       {"title": "Registo de Horas — Movimentação de Viaturas", "file": "registo-horas-movimentacao.html", "icon": "🕘", "section": "Colaborador",
                            "kw": "registo horas movimentacao viaturas prestador prestacao servicos gilson recibo verde fatura recibo contabilidade valor hora avenca folha de horas transporte viaturas"},
    "simulador_horas":     {"title": "Simulador de Horas de Pintura",            "file": "simulador-horas-pintura.html",      "icon": "🎨", "section": "Operações",
                            "kw": "simulador horas pintura mop mpi tinta valor hora preparacao osv osvs orcamento colisao chapa calculo horas mao de obra pintor repartir horas"},
    # ---- Coordenação ----
    "coord_divergencias":  {"title": "Divergências Picagens",                   "file": "coord_divergencias.html",            "icon": "📊", "section": "Coordenação",
                            "kw": "divergencias picagens validar relogio ponto coordenador"},
    "coord_estatisticas":  {"title": "Estatísticas Picagens",                   "file": "coord_estatisticas.html",            "icon": "📈", "section": "Coordenação",
                            "kw": "estatisticas picagens ponto historico tecnicos"},
    "coord_inspecao_diaria":{"title": "Checklist Inspeção Diária",              "file": "checklist_inspecao_diaria.html",     "icon": "✅", "section": "Coordenação",
                            "kw": "inspecao diaria checklist abertura oficina verificacao"},
    "coord_auditoria_carrinhos": {"title": "Auditorias Carrinhos Ferramentas Mensal", "file": "auditoria-carrinhos-ferramentas.html", "icon": "🧰", "section": "Coordenação",
                            "kw": "carrinho ferramentas auditoria mensal atas inventario tecnico caixa"},
    "aval_merito":         {"title": "Avaliações de Mérito",                    "file": "avaliacoes-merito.html",             "icon": "⭐", "section": "Coordenação",
                            "kw": "avaliacao merito mecatronicos tecnicos nivel classificacao mensal coordenador"},
    "parecer_merito":      {"title": "Parecer Avaliações Mérito Equipas",       "file": "parecer-avaliacoes-merito.html",     "icon": "📋", "section": "Coordenação",
                            "kw": "parecer merito equipas assessores fieis armazem apreciacao coordenador"},
    "prep_auditoria_sqa_bcs":{"title": "Preparação Auditoria SQA - Bosch Car Service","file":"Checklist_Auditoria_SQA_BCS.html","icon": "🔍", "section": "Coordenação",
                            "kw": "auditoria sqa bosch car service preparacao checklist"},
    "equipamentos":        {"title": "Manutenção de Equipamentos",              "file": "manutencao-equipamentos.html",       "icon": "🛠️", "section": "Coordenação",
                            "kw": "equipamentos manutencao elevadores maquinas calibracao revisao"},
    # ---- Administração ----
    "coord_inspecoes":     {"title": "Auditoria Interna Trimestral",            "file": "checklist_auditoria_trimestral.html","icon": "🔍", "section": "Administração",
                            "kw": "auditoria interna trimestral checklist"},
    "officegest_api":      {"title": "API Officegest (Consola)",                "file": "officegest-api-explorer.html",       "icon": "🔧", "section": "Administração",
                            "kw": "api officegest consola explorador dados"},
    "fardas":              {"title": "Gestão de Fardas",                        "file": "fardas.html",                        "icon": "👕", "section": "Administração",
                            "kw": "fardas fardamento uniformes polo sweat casaco calcas tamanhos entrega stock roupa"},
    "termos_responsabilidade": {"title": "Termos de Responsabilidade",          "file": "termos-responsabilidade.html",       "icon": "📄", "section": "Administração",
                            "kw": "termo responsabilidade assinatura equipamento carrinho telemovel entrega"},
    "aval_merito_admin":   {"title": "Avaliações de Mérito (Equipas)",          "file": "avaliacoes-merito-admin.html",       "icon": "⭐", "section": "Administração",
                            "kw": "avaliacao merito assessores vendas fieis armazem coordenadores admin"},
    "guiao_entrevista":    {"title": "Guião de Entrevista (Enquadramento)",     "file": "guiao-entrevista-enquadramento.html","icon": "🎙️", "section": "Administração",
                            "kw": "guiao entrevista recrutamento candidato tecnico mecanico enquadramento escalao admissao competencias cotacao"},
    "margem":              {"title": "Cálculo Margem Provisória Mensal",        "file": "margem-provisoria.html",             "icon": "💰", "section": "Administração",
                            "kw": "margem provisoria mensal calculo vendas custos resultado"},
    "divergencias":        {"title": "Divergências Picagens OG vs 2Smart",      "file": "divergencias-picagens.html",         "icon": "📊", "section": "Administração",
                            "kw": "divergencias picagens officegest 2smart gerar relatorios"},
    "kpis_coord":          {"title": "Gerador Relatórios KPIs Coordenação",     "file": "gerador-kpis.html",                  "icon": "📈", "section": "Administração",
                            "kw": "kpis gerador relatorios eficiencia utilizacao horas semanas"},
    "verificador_garantias": {"title": "Verificador de Faturas de Garantia",    "file": "verificador-garantias.html",         "icon": "🛡️", "section": "Administração",
                            "kw": "garantias faturas verificador prazo legal"},
    "verificador_orcamentos": {"title": "Verificação de Orçamentos",            "file": "verificador-orcamentos.html",        "icon": "🧾", "section": "Administração",
                            "kw": "orcamentos verificacao aprovacao pendentes"},
    "analisador_os":       {"title": "Analisador de Ordens de Serviço",         "file": "analisador-os.html",                 "icon": "🛠️", "section": "Administração",
                            "kw": "ordens servico os analisador abertas fechadas"},
    "auditoria_oficina":   {"title": "Auditoria Mensal da Oficina",             "file": "auditoria-oficina.html",             "icon": "🔎", "section": "Administração",
                            "kw": "auditoria mensal oficina os amostra verificacao"},
    "google_reviews":      {"title": "Google Reviews",                          "file": "google-reviews.html",                "icon": "⭐", "section": "Administração",
                            "kw": "google reviews avaliacoes clientes estrelas reputacao"},
    "questionario_satisfacao": {"title": "Questionário de Satisfação",          "file": "questionario-satisfacao.html",       "icon": "📝", "section": "Administração",
                            "kw": "questionario satisfacao inquerito clientes nps"},
    "conferencia_faturas": {"title": "Conferência de Faturas Ayvens vs OfficeGest", "file": "conferencia-faturas-ayvens.html","icon": "📑", "section": "Administração",
                            "kw": "conferencia faturas ayvens officegest comparacao"},
    "conferencia_os_orc":  {"title": "Conferência OS vs Orçamentos",            "file": "conferencia-os-orcamentos.html",     "icon": "🔍", "section": "Administração",
                            "kw": "conferencia os orcamentos comparar valores"},
}

# Sub-entradas: cada uma vira uma entrada separada no índice de pesquisa.
# Quando o utilizador clica, openModule(parentId, subId) faz iframe.src = url + '#sub=' + subId
SUB_ENTRIES = {
    "indicadores_obj": [
        {"sub": "kpis",          "icon": "📈", "title": "KPIs Coordenação",                  "desc": "Indicadores-chave de desempenho por unidade — horas, eficiência produtiva e utilização."},
        {"sub": "ticket",        "icon": "🎫", "title": "Ticket Médio",                       "desc": "Valor médio por ordem de serviço — peças, mão-de-obra e total."},
        {"sub": "margem",        "icon": "💰", "title": "Margem Mensal",                      "desc": "Margem operacional mensal — vendas, custos fixos/variáveis e resultado líquido."},
        {"sub": "taxa_retencao", "icon": "🚗", "title": "Análise Taxa Retenção Viaturas",     "desc": "Crescimento e retenção de matrículas — novas, regressadas, perdidas e taxa de retenção anual."},
        {"sub": "mapa_clientes", "icon": "🗺️", "title": "Mapa de Clientes",                   "desc": "Globo interativo com a distribuição geográfica da carteira — filtros por unidade (Cacém/Lisboa/Colisão) e ano de registo."},
    ],
    "recursos_humanos": [
        {"sub": "ferias",      "icon": "🏖️", "title": "Férias e Faltas",                   "desc": "Marcação de férias, gestão de faltas e justificações."},
        {"sub": "formacao",    "icon": "🎓", "title": "Formação",                          "desc": "Plano de formação anual e pedidos de formação."},
        {"sub": "documentos",  "icon": "📄", "title": "Documentos RH",                     "desc": "Recibos, certificados, declarações e outros documentos pessoais."},
        {"sub": "info",        "icon": "ℹ️", "title": "Informações Úteis RH",              "desc": "Seguro de acidentes de trabalho, medicina no trabalho, subsídios, procedimento em caso de acidente de trabalho, contactos de RH."},
        {"sub": "validacoes",  "icon": "✅", "title": "Validações Divergências",           "desc": "Relatórios de divergências validados pelos coordenadores."},
    ],
}

def strip_html(text):
    text = re.sub(r"<script[\s\S]*?</script>", " ", text, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_headings(raw):
    out, seen = [], set()
    for h in re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", raw, flags=re.I | re.S):
        c = strip_html(h)
        if c and len(c) <= 120 and c.lower() not in seen:
            out.append(c); seen.add(c.lower())
    return out

index = []
missing = []
for mod_id, info in MODULES.items():
    f = ROOT / info["file"]
    if not f.exists():
        print(f"WARNING: missing {f}")
        missing.append(mod_id)
        continue
    raw = f.read_text(encoding="utf-8", errors="ignore")
    plain = strip_html(raw)
    headings = extract_headings(raw)
    # Palavras-chave entram nos headings (peso alto na pesquisa do widget)
    kw = info.get("kw", "")
    if kw:
        headings = [kw] + headings

    index.append({
        "id": mod_id,
        "title": info["title"],
        "section": info["section"],
        "icon": info["icon"],
        "headings": headings[:60],
        "content": plain[:40000],
    })

    for sub in SUB_ENTRIES.get(mod_id, []):
        content_chunks = [sub["desc"]]
        title_norm = sub["title"].lower()
        for para in re.split(r"\s{2,}|\.\s", plain):
            if title_norm in para.lower() and len(para) < 400:
                content_chunks.append(para)
        index.append({
            "id": mod_id,
            "subId": sub["sub"],
            "title": sub["title"],
            "section": info["title"],
            "icon": sub["icon"],
            "headings": [],
            "content": " · ".join(content_chunks)[:4000],
        })

# Fallback: módulos cujo ficheiro não existe localmente mantêm a entrada do índice antigo
old_index_path = ROOT / "search-index.js"
if missing and old_index_path.exists():
    old_raw = old_index_path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"window\.SEARCH_INDEX\s*=\s*(\[[\s\S]*\]);", old_raw)
    if m:
        try:
            old_entries = json.loads(m.group(1))
            for e in old_entries:
                if e.get("id") in missing and "subId" not in e:
                    index.append(e)
                    print(f"  (reaproveitada entrada antiga: {e['id']})")
        except Exception as ex:
            print("  fallback índice antigo falhou:", ex)

out_js = "window.SEARCH_INDEX = " + json.dumps(index, ensure_ascii=False) + ";"
out_path = ROOT / "search-index.js"
out_path.write_text(out_js, encoding="utf-8")
print(f"Wrote index with {len(index)} entries ({sum(1 for e in index if 'subId' not in e)} módulos + {sum(1 for e in index if 'subId' in e)} sub-entradas)")
print(f"Index size: {len(out_js):,} chars ({len(out_js)/1024:.1f} KB)")
