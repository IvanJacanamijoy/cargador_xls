import { useState, useEffect } from 'react'
import type { ChangeEvent } from 'react'
import axios from 'axios'

interface UploadedRow {
  codigo_cliente?: string
  nombre_completo?: string
  fecha_nacimiento?: string
  direccion?: string
  localidad_cp?: string
  telefono?: string
  email?: string
  fecha_alta?: string
  grupo_clientes?: string
  batch_id?: string
}

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [uploadedData, setUploadedData] = useState<UploadedRow[]>([])
  const [batchId, setBatchId] = useState<string | null>(null)
  const [availableBatches, setAvailableBatches] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(0)
  const rowsPerPage = 30

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        const res = await axios.get(`${import.meta.env.VITE_API_URL}/upload/batches`)
        const batches = res.data.map((b: { batch_id: string }) => b.batch_id)
        setAvailableBatches(batches)
      } catch (err) {
        console.error('Error al obtener lotes:', err)
      }
    }

    fetchBatches()
  }, [])


  const paginatedData = uploadedData.slice(
    currentPage * rowsPerPage,
    (currentPage + 1) * rowsPerPage
  )
  const totalPages = Math.ceil(uploadedData.length / rowsPerPage)

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    try {
      const formData = new FormData()
      formData.append('file', file)

      const initRes = await axios.post(`${import.meta.env.VITE_API_URL}/upload/init`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) {
            const percent = Math.round((e.loaded * 100) / e.total)
            setProgress(percent)
          }
        }
      })

      const batch = initRes.data.batch_id
      setBatchId(batch)

      await axios.post(`${import.meta.env.VITE_API_URL}/upload/process/${batch}`)

      const dataRes = await axios.get(`${import.meta.env.VITE_API_URL}/data/batch/${batch}?limit=1000`)
      setUploadedData(dataRes.data || [])
      setCurrentPage(0)

    } catch (err) {
      console.error('Error en la carga:', err)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto flex flex-col gap-6">
        {/* Sección 1: Carga de archivo */}
        <div className="bg-white p-6 rounded shadow flex flex-col">
          <h2 className="text-xl font-bold mb-4 text-center">📤 Cargar archivo</h2>
          <input type="file" accept=".xls,.xlsx" onChange={handleFileChange} className="mb-4 block border w-60 mx-auto pl-4 py-4 rounded-xl bg-gray-100 cursor-pointer hover:bg-gray-200" />
          <button
            onClick={handleUpload}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-40 mx-auto cursor-pointer"
          >
            Subir archivo
          </button>

          {progress > 0 && (
            <div className="mt-4">
              <div className="text-sm text-gray-600 mb-1">Progreso: {progress}%</div>
              <div className="w-full bg-gray-200 rounded-full h-4">
                <div
                  className="bg-green-500 h-4 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Selector de lote */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Seleccionar lote:</label>
          <select
            value={batchId ?? ''}
            onChange={async (e) => {
              const selected = e.target.value
              setBatchId(selected)
              setCurrentPage(0)
              try {
                const res = await axios.get(`${import.meta.env.VITE_API_URL}/data/batch/${selected}?limit=1000`)
                setUploadedData(res.data || [])
              } catch (err) {
                console.error('Error al cargar lote:', err)
              }
            }}
            className="w-full border rounded px-2 py-1"
          >
            <option value="">-- Selecciona un lote --</option>
            {availableBatches.map((b) => (
              <option key={b} value={b}>{b}</option>
            ))}
          </select>
        </div>


        {/* Sección 2: Datos cargados */}
        <div className="bg-white p-6 rounded shadow overflow-auto">
          <h2 className="text-xl font-bold mb-4">📊 Datos cargados</h2>
          {uploadedData.length === 0 ? (
            <p className="text-gray-500">No hay datos cargados aún.</p>
          ) : (
            <>
              <table className="table-auto w-full text-sm">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="px-2 py-1 text-left">Código</th>
                    <th className="px-2 py-1 text-left">Nombre</th>
                    <th className="px-2 py-1 text-left">Nacimiento</th>
                    <th className="px-2 py-1 text-left">Dirección</th>
                    <th className="px-2 py-1 text-left">Localidad</th>
                    <th className="px-2 py-1 text-left">Teléfono</th>
                    <th className="px-2 py-1 text-left">Email</th>
                    <th className="px-2 py-1 text-left">Alta</th>
                    <th className="px-2 py-1 text-left">Grupo</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedData.map((row, idx) => (
                    <tr key={idx} className="border-t">
                      <td className="px-2 py-1">{row.codigo_cliente ?? '-'}</td>
                      <td className="px-2 py-1">{row.nombre_completo ?? '-'}</td>
                      <td className="px-2 py-1">{row.fecha_nacimiento ?? '-'}</td>
                      <td className="px-2 py-1">{row.direccion ?? '-'}</td>
                      <td className="px-2 py-1">{row.localidad_cp ?? '-'}</td>
                      <td className="px-2 py-1">{row.telefono ?? '-'}</td>
                      <td className="px-2 py-1">{row.email ?? '-'}</td>
                      <td className="px-2 py-1">{row.fecha_alta ?? '-'}</td>
                      <td className="px-2 py-1">{row.grupo_clientes ?? '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Controles de paginación */}
              <div className="flex justify-between items-center mt-4">
                <button
                  onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 0))}
                  disabled={currentPage === 0}
                  className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
                >
                  ← Anterior
                </button>
                <span className="text-sm text-gray-600">
                  Página {currentPage + 1} de {totalPages}
                </span>
                <button
                  onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages - 1))}
                  disabled={currentPage >= totalPages - 1}
                  className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
                >
                  Siguiente →
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
