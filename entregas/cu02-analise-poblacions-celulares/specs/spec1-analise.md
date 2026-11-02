# Spec 1: Análise

## Motor de análise bioinformática, cruzamento multivariante e interpretación vía LLM

### Que construír
O núcleo lóxico e de procesamento do sistema (orientado ao backend e á integración co LLM) que abrangue catro procesos:
1. **Inxesta e normalización:** Lectura de ficheiros en formato diverso ('.xlsx', '.csv', '.tsv', '.txt'), mapeo automático de columnas mediante dicionarios de sinónimos, inferencia do tipo celular (limpando termos xenéricos e prefixos do nome do ficheiro) e da colección (Hallmark, KEGG, Reactome, GO) cando polo menos o 50 % das rutas compartan o prefixo correspondente (asignando 'Coleccion 1' por defecto en caso contrario), e división da cadea de xenes de 'core_enrichment'.
2. **Clasificación de patróns:** Filtrado das rutas segundo os limiares activos ('p axustado' máximo, '|NES|' mínimo, sentido e busca por texto) e clasificación de cada ruta significativa en 'mismo sentido' (significativa en 2 ou máis tipos celulares, todos co mesmo signo de NES), 'sentido opuesto' (significativa en 2 ou máis tipos celulares onde polo menos un presenta signo de NES distinto aos demais) ou 'especifica' (significativa nun único tipo celular).
3. **Similitude, solapamento e recorrencia xénica:**
   - Cálculo do Índice de Jaccard con signo entre cada parella de tipos celulares.
   - Cálculo da intersección de xenes do 'core_enrichment' (tanto global entre todos os tipos onde a ruta é significativa como por parellas), obtendo a porcentaxe sobre a unión e sobre o conxunto menor, así como unha matriz de presenza/ausencia por xene e tipo celular vinculada ao signo do NES.
   - Agregación transversal de xenes recorrentes en todas as rutas significativas, contabilizando en cantos tipos celulares distintos e en cantas rutas participa cada xene.
4. **Pipeline de IA verificada:** Xeración dun obxecto JSON estruturado cos feitos matemáticos arredondados que alimenta a un LLM para redactar unha interpretación, seguido dun validador determinista que extrae todas as cifras do texto xerado e comproba que existan no JSON orixinal.

### Por que
Este tipo de análises son útiles en diferentes investigacións e ata o momento estaban sendo levadas a cabo de forma artesanal para cada grupo de exemplos. O cumprimento desta especificación implicaría a automatización de ditas análises, supoñendo un apoio á hora de extraer patróns estatísticos que aforra tempo da persoa investigadora.

### Restricións
- **Inmutabilidade estatística:** O motor nunca recalcula ningún p-valor, q-valor nin NES; emprega estritamente os valores numéricos xa calculados nos ficheiros de orixe. As porcentaxes de xenes comúns son descritivas e non representan un test estatístico.
- **Regras de validación e suplencia en arquivos:**
  - Un ficheiro require obrigatoriamente columnas para ruta, 'NES' e unha métrica de significancia. As filas sen estes datos ignóranse.
  - A métrica de significancia segue unha xerarquía estrita de prioridade: busca primeiro 'p axustado' ('padj'/'fdr'); se non existe, emprega 'q-valor'; e como último recurso 'p-valor' nominal, xerando unha advertencia explícita de que o valor pode non estar corrixido por tests múltiples.
  - Se hai rutas duplicadas nun mesmo ficheiro ou ao combinar varios ficheiros dun mesmo tipo celular e colección, sobrescríbese o índice conservando estritamente a última aparición.
  - A columna de xenes divídese con prioridade polo carácter '/' se está presente na cadea; só en ausencia de '/' se divide por comas, puntos e comas ou espazos en branco.
- **Fórmula de Jaccard e casos límite:** A similitude entre os tipos A e B calcúlase como J(A,B) = concordantes / (nA + nB - concordantes). Se nA = 0 ou nB = 0, o resultado debe ser 'null' (non calculable) para evitar divisións por cero ou falsos ceros.
- **Arredondamento no JSON de feitos e tolerancia do LLM verificador:**
  - Ao construír o obxecto JSON para o LLM, os valores de 'NES' e 'Jaccard' expórtanse arredondados a 2 decimais, o 'p axustado' a 2 cifras significativas, e as porcentaxes de solapamento xénico arredóndanse ao enteiro máis próximo.
  - O validador debe buscar no texto xerado polo LLM todos os números decimais (d+ undescore d+) e porcentaxes (d+ %). Unha porcentaxe só é válida se coincide exactamente cun enteiro do JSON de feitos; un decimal é válido se a diferenza absoluta entre o seu valor absoluto e algún número do JSON é menor ou igual a 0.0051.

### Criterios de aceptación
- Ao procesar un ficheiro '.csv' con cabeceiras 'Description', 'NormalizedEnrichmentScore', 'FDR' e 'core_enrichment' (con xenes separados por '/'), o motor mapea automaticamente os campos sen erros, infire a colección 'Hallmark' se polo menos a metade das rutas comezan por 'HALLMARK_' e extrae a lista de xenes. Se o ficheiro só trouxese 'pvalue' en lugar de 'FDR', úsao como métrica de significancia e rexistra un aviso.
- Dadas tres listas de rutas filtradas onde HALLMARK_MYOGENESIS ten NES -2.12, -1.77 e -2.36, e HALLMARK_TNFA_SIGNALING_VIA_NFKB ten NES +1.49, +1.63 e -1.65, o motor clasifica a primeira como 'mismo sentido' e a segunda como 'sentido opuesto'.
- Se o Tipo A ten 10 rutas significativas e o Tipo B ten 13, compartindo 3 rutas co mesmo signo de NES, o cálculo de similitude devolve exactamente 0.15 (3 / (10 + 13 - 3)); se un terceiro Tipo C ten 0 rutas significativas, a súa similitude con A e B devolve 'null'.
- Na agregación transversal de xenes, se o xene 'IRF7' aparece no 'core_enrichment' de 3 rutas significativas distribuídas en 4 tipos celulares, o motor rexistra 'IRF7' con presenza en 4 tipos e 3 rutas, ordenando a táboa global primeiro por número de tipos celulares (descendente) e despois por número de rutas.
- Se o texto devolto polo LLM contén unha cifra decimal que non se corresponde con ningún valor do JSON de feitos (con marxe menor ou igual a 0.0051) ou unha porcentaxe que não coincide exactamente cun enteiro do JSON, a función de verificación devolve esa cifra na lista de erros indicando cantas cifras totais foron comprobadas.
