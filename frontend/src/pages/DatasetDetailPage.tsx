import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { datasetService } from '@/services/datasetService';
import { customChallengeService } from '@/services/customChallengeService';
import type { DatasetDetailResponse, CustomChallengeListItem } from '@/types';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export function DatasetDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [dataset, setDataset] = useState<DatasetDetailResponse | null>(null);
  const [challenges, setChallenges] = useState<CustomChallengeListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadDatasetDetails(parseInt(id));
      loadChallenges(parseInt(id));
    }
  }, [id]);

  const loadDatasetDetails = async (datasetId: number) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await datasetService.getDatasetDetail(datasetId);
      setDataset(data);
    } catch (err) {
      setError('Failed to load dataset details');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadChallenges = async (datasetId: number) => {
    try {
      const response = await customChallengeService.getChallenges({
        dataset_id: datasetId,
      });
      setChallenges(response.challenges);
    } catch (err) {
      console.error('Failed to load challenges:', err);
    }
  };

  const handleDelete = async () => {
    if (!dataset || !id) return;

    const confirmMsg = challenges.length > 0
      ? `Delete "${dataset.name}" and ${challenges.length} associated challenge(s)?`
      : `Delete "${dataset.name}"?`;

    if (!confirm(confirmMsg)) return;

    try {
      await datasetService.deleteDataset(parseInt(id));
      navigate('/datasets');
    } catch (err) {
      alert('Failed to delete dataset');
      console.error(err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !dataset) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-red-600">{error || 'Dataset not found'}</p>
        <Button onClick={() => navigate('/datasets')}>Back to Datasets</Button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">{dataset.name}</h1>
            {dataset.description && (
              <p className="text-gray-600">{dataset.description}</p>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="primary"
              onClick={() => navigate(`/challenges/custom/new?dataset=${dataset.id}`)}
            >
              Create Challenge
            </Button>
            <Button variant="danger" onClick={handleDelete}>
              Delete Dataset
            </Button>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex gap-6 text-sm text-gray-600">
          <div>
            <span className="font-medium">Table:</span>{' '}
            <code className="bg-gray-100 px-2 py-1 rounded">{dataset.table_name}</code>
          </div>
          <div>
            <span className="font-medium">Rows:</span> {dataset.row_count.toLocaleString()}
          </div>
          <div>
            <span className="font-medium">Challenges:</span> {challenges.length}
          </div>
          <div>
            <span className="font-medium">Uploaded:</span>{' '}
            {new Date(dataset.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>

      {/* Schema */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Schema</h2>
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Column Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Data Type
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {dataset.schema.columns.map((col, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                    {col.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {col.type}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Sample Data */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Sample Data (First 10 Rows)</h2>
        {dataset.sample_data.length > 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  {dataset.schema.columns.map((col) => (
                    <th
                      key={col.name}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                    >
                      {col.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {dataset.sample_data.map((row, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    {dataset.schema.columns.map((col) => (
                      <td
                        key={col.name}
                        className="px-6 py-4 whitespace-nowrap text-sm text-gray-900"
                      >
                        {row[col.name] ?? 'NULL'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-600 text-center py-8 bg-gray-50 rounded-lg">
            No sample data available
          </p>
        )}
      </div>

      {/* Associated Challenges */}
      <div>
        <h2 className="text-xl font-semibold mb-4">
          Challenges Using This Dataset ({challenges.length})
        </h2>
        {challenges.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {challenges.map((challenge) => (
              <div
                key={challenge.id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <h3 className="font-semibold mb-2 line-clamp-2">{challenge.title}</h3>
                <div className="flex gap-2 mb-3">
                  <span className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded capitalize">
                    {challenge.difficulty}
                  </span>
                  <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                    {challenge.points} pts
                  </span>
                  {!challenge.is_active && (
                    <span className="text-xs bg-red-50 text-red-600 px-2 py-1 rounded">
                      Inactive
                    </span>
                  )}
                </div>
                <div className="text-sm text-gray-600 mb-3">
                  <div className="flex justify-between">
                    <span>Submissions:</span>
                    <span>{challenge.submission_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Success Rate:</span>
                    <span>{challenge.completion_rate.toFixed(1)}%</span>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/challenges/custom/${challenge.id}`)}
                  className="w-full"
                >
                  View Challenge
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 bg-gray-50 rounded-lg">
            <p className="text-gray-600 mb-4">No challenges created for this dataset yet</p>
            <Button onClick={() => navigate(`/challenges/custom/new?dataset=${dataset.id}`)}>
              Create First Challenge
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
