import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { datasetService } from '@/services/datasetService';
import type { DatasetListItem } from '@/types';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export function DatasetsPage() {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await datasetService.getDatasets();
      setDatasets(response.datasets);
    } catch (err) {
      setError('Failed to load datasets');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this dataset and all associated challenges?')) {
      return;
    }

    try {
      await datasetService.deleteDataset(id);
      await loadDatasets();
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

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <p className="text-red-600">{error}</p>
        <Button onClick={loadDatasets}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold">My Datasets</h1>
          <p className="text-gray-600 mt-2">Upload CSV files to create custom challenges</p>
        </div>
        <Button onClick={() => navigate('/datasets/upload')}>
          Upload Dataset
        </Button>
      </div>

      {datasets.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">No datasets yet</h3>
          <p className="text-gray-600 mb-4">Upload a CSV file to get started</p>
          <Button onClick={() => navigate('/datasets/upload')}>
            Upload Your First Dataset
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {datasets.map((dataset) => (
            <div
              key={dataset.id}
              className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <h3 className="font-semibold text-lg mb-2">{dataset.name}</h3>
              {dataset.description && (
                <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                  {dataset.description}
                </p>
              )}

              <div className="space-y-2 text-sm text-gray-500 mb-4">
                <div className="flex justify-between">
                  <span>Rows:</span>
                  <span className="font-medium">{dataset.row_count.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Challenges:</span>
                  <span className="font-medium">{dataset.challenge_count}</span>
                </div>
                <div className="flex justify-between">
                  <span>Uploaded:</span>
                  <span className="font-medium">
                    {new Date(dataset.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/datasets/${dataset.id}`)}
                  className="flex-1"
                >
                  View
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigate(`/challenges/custom/new?dataset=${dataset.id}`)}
                  className="flex-1"
                >
                  Create Challenge
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => handleDelete(dataset.id)}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
