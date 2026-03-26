# Resumo das Estações e Unidades Móveis da Zona Oeste

## Visão geral

- As estações fixas de `Bangu`, `Campo Grande` e `Pedra de Guaratiba` têm base temporal muito estável, com cobertura longa e poucos ou nenhum problema de calendário.
- As unidades móveis de `Bangu` e `Recreio` funcionam mais como bases de campanha: são úteis, mas cobrem janelas curtas e têm maior limitação de sensores e completude.
- O principal gargalo geral não está na linha do tempo das bases, mas na disponibilidade desigual entre variáveis e sensores.

## Bangu

- Estação fixa com base muito consistente de `2012` a `2018`, sem falhas temporais relevantes.
- Melhor cobertura em `chuva`, `ur`, `o3`, `co`, `no`, `no2` e `nox`.
- `pm2_5` está indisponível, e `temp`, `so2` e `pm10` exigem mais cautela por incompletude.
- É uma estação forte para análises temporais amplas e para investigar episódios elevados de poluentes.

## Campo Grande

- Estação fixa com base muito consistente de `2012` a `2018`, sem falhas relevantes no calendário.
- `temp` e `chuva` são as variáveis mais completas.
- `ur` é a variável mais crítica em completude, e `pm2_5` está indisponível.
- Chama atenção o comportamento mais intenso de `nox` e `no`, sugerindo episódios concentrados de poluição.

## Pedra de Guaratiba

- Estação fixa com base muito estável, com apenas `1` timestamp faltante no período.
- O conjunto de poluentes disponível é bem mais restrito do que nas outras estações.
- `co`, `no`, `no2`, `nox`, `pm2_5` e `so2` estão indisponíveis.
- A estação é mais útil para estudar `o3`, `pm10`, `temp`, `chuva` e, com mais cautela, `ur`.

## Unidade Móvel Bangu

- Base curta, cobrindo `2016-12` a `2017-09`, com `45` timestamps faltantes.
- `chuva`, `temp` e `ur` têm excelente completude.
- `no`, `no2`, `nox` e `pm10` estão indisponíveis.
- `so2`, `pm2_5` e `o3` são aproveitáveis, mas pedem mais controle de completude.

## Unidade Móvel Recreio

- Base curta, cobrindo `2017-10` a `2018-03`, com `30` timestamps faltantes.
- `temp`, `chuva` e `co` são as variáveis mais confiáveis.
- `no`, `no2`, `nox` e `pm10` estão indisponíveis.
- `pm2_5` é a variável mais crítica entre as disponíveis, enquanto `o3` e `so2` ainda têm utilidade analítica com cautela.

## Síntese final

- `Bangu` e `Campo Grande` aparecem como as bases mais completas para análises multivariadas mais ricas.
- `Pedra de Guaratiba` é útil, mas com capacidade analítica concentrada em menos variáveis.
- As unidades móveis complementam o monitoramento, mas devem ser tratadas como séries de campanha, não como séries longas equivalentes às estações fixas.