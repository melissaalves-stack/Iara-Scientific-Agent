import L from "leaflet";
import { useMemo } from "react";
import { GeoJSON, MapContainer, Marker, TileLayer, Tooltip, ZoomControl } from "react-leaflet";
import type { Camadas } from "../api";
import { CLASSIFICACOES, type Classificacao, type Registro } from "../types";
import { IconeStatus, pinoSvg } from "./Marca";

interface Props {
  registros: Registro[];
  camadas: Camadas;
  selecionado: string | null;
  onSelecionar: (id: string) => void;
}

const COR_PENDENTE = "#3D4A41";

function icone(r: Registro, ativo: boolean) {
  const cor = r.classificacao ? CLASSIFICACOES[r.classificacao].cor : COR_PENDENTE;
  const w = ativo ? 40 : 30;
  const h = Math.round(w * 1.3);
  return L.divIcon({
    className: "pino",
    html: pinoSvg(cor, r.classificacao, ativo),
    iconSize: [w, h],
    iconAnchor: [w / 2, h - 1],
    tooltipAnchor: [0, -h + 6],
  });
}

function municipio(r: Registro): string | null {
  const geo = r.pareceres.find((p) => p.agente === "geoespacial")?.detalhes;
  return geo?.municipio ? `${geo.municipio}/${geo.uf}` : null;
}

export default function Mapa({ registros, camadas, selecionado, onSelecionar }: Props) {
  const icones = useMemo(
    () => Object.fromEntries(registros.map((r) => [r.id, icone(r, r.id === selecionado)])),
    [registros, selecionado],
  );

  return (
    <div className="mapa-moldura">
      <MapContainer center={[-3.4, -58]} zoom={5} className="mapa" zoomControl={false}>
        <ZoomControl position="topright" />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        {camadas.amazonia_legal && (
          <GeoJSON data={camadas.amazonia_legal} style={{ color: "#1F4A33", weight: 1.6, fillOpacity: 0, dashArray: "6 5" }} interactive={false} />
        )}
        {camadas.areas_protegidas && (
          <GeoJSON
            data={camadas.areas_protegidas}
            style={{ color: "#6E9C7A", weight: 0.7, fillColor: "#BFD6C1", fillOpacity: 0.55 }}
            onEachFeature={(f, layer) => layer.bindTooltip(`${f.properties?.nome ?? ""} · ${f.properties?.categoria ?? "UC"}`)}
          />
        )}
        {camadas.terras_indigenas && (
          <GeoJSON
            data={camadas.terras_indigenas}
            style={{ color: "#8C6A45", weight: 1, fillOpacity: 0, dashArray: "3 4" }}
            onEachFeature={(f, layer) => layer.bindTooltip(`Terra Indígena ${f.properties?.nome ?? ""}`)}
          />
        )}
        {camadas.rios_principais && (
          <GeoJSON
            data={camadas.rios_principais}
            style={{ color: "#1D3B4F", weight: 1.4, opacity: 0.85 }}
            onEachFeature={(f, layer) => layer.bindTooltip(`Rio ${f.properties?.nome ?? ""}`)}
          />
        )}

        {registros.map((r) => (
          <Marker
            key={r.id}
            position={[r.latitude, r.longitude]}
            icon={icones[r.id]}
            zIndexOffset={r.id === selecionado ? 1000 : 0}
            eventHandlers={{ click: () => onSelecionar(r.id) }}
            keyboard
            title={r.nome_popular}
          >
            <Tooltip direction="top" className="tooltip-registro" permanent={r.id === selecionado}>
              <strong>{r.nome_popular}</strong>
              <span>
                {r.classificacao ? CLASSIFICACOES[r.classificacao].rotulo : "Aguardando comitê"}
                {municipio(r) && ` · ${municipio(r)}`}
                {r.score_consistencia !== null && ` · ${r.score_consistencia}/100`}
              </span>
            </Tooltip>
          </Marker>
        ))}
      </MapContainer>

      <div className="legenda">
        <strong>Legenda</strong>
        {(Object.keys(CLASSIFICACOES) as Classificacao[]).map((c) => (
          <div key={c} className="legenda-item">
            <span className="legenda-pino" style={{ background: CLASSIFICACOES[c].cor }}>
              <IconeStatus status={c} cor="#fff" tamanho={10} />
            </span>
            {CLASSIFICACOES[c].rotulo}
          </div>
        ))}
        <hr />
        <div className="legenda-item"><span className="legenda-uc" />Unidade de conservação</div>
        <div className="legenda-item"><span className="legenda-ti" />Terra indígena</div>
        <div className="legenda-item"><span className="legenda-al" />Amazônia Legal</div>
      </div>
      <div className="creditos-camadas">MMA · IBGE · CNUC · FUNAI · Natural Earth</div>
    </div>
  );
}
