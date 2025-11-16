import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { datasetService } from '@/services/datasetService';
import type { DatasetResponse } from '@/types';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const uploadSchema = z.object({
  name: z.string().min(1, 'Name is required').max(200, 'Name too long'),
  description: z.string().max(1000, 'Description too long').optional(),
});

type UploadFormData = z.infer<typeof uploadSchema>;

export function DatasetUploadPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedDataset, setUploadedDataset] = useState<DatasetResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema),
    mode: 'onBlur',
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file
    if (!file.name.endsWith('.csv')) {
      setError('Please select a CSV file');
      setSelectedFile(null);
      return;
    }

    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      setError('File is too large. Maximum size is 5MB');
      setSelectedFile(null);
      return;
    }

    setError(null);
    setSelectedFile(file);
  };

  const onSubmit = async (data: UploadFormData) => {
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    try {
      setIsUploading(true);
      setError(null);

      const dataset = await datasetService.uploadDataset(
        selectedFile,
        data.name,
        data.description
      );

      setUploadedDataset(dataset);
    } catch (err: any) {
      setError(err.message || 'Failed to upload dataset');
      console.error(err);
    } finally {
      setIsUploading(false);
    }
  };

  // Show success screen after upload
  if (uploadedDataset) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
          <div className="text-green-600 text-5xl mb-4">✓</div>
          <h2 className="text-2xl font-bold mb-2">Dataset Uploaded Successfully!</h2>
          <p className="text-gray-600 mb-6">
            {uploadedDataset.name} with {uploadedDataset.row_count} rows
          </p>

          <div className="bg-white border rounded-lg p-4 mb-6 text-left">
            <h3 className="font-semibold mb-2">Dataset Schema</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {uploadedDataset.schema.columns.map((col) => (
                <div key={col.name} className="flex justify-between border-b pb-1">
                  <span className="font-mono">{col.name}</span>
                  <span className="text-gray-600">{col.type}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-4 justify-center">
            <Button onClick={() => navigate('/datasets')}>
              View All Datasets
            </Button>
            <Button
              variant="primary"
              onClick={() => navigate(`/challenges/custom/new?dataset=${uploadedDataset.id}`)}
            >
              Create Challenge
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Upload Dataset</h1>
        <p className="text-gray-600">
          Upload a CSV file to create custom SQL challenges
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* File Upload */}
        <div>
          <label className="block text-sm font-medium mb-2">
            CSV File *
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
              disabled={isUploading}
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer"
            >
              {selectedFile ? (
                <div>
                  <div className="text-green-600 text-4xl mb-2">📄</div>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                  <p className="text-sm text-blue-600 mt-2">
                    Click to change file
                  </p>
                </div>
              ) : (
                <div>
                  <div className="text-gray-400 text-4xl mb-2">📤</div>
                  <p className="text-gray-600">
                    Click to select a CSV file
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    Max 5MB, up to 10,000 rows
                  </p>
                </div>
              )}
            </label>
          </div>
        </div>

        {/* Dataset Name */}
        <Input
          label="Dataset Name *"
          {...register('name')}
          error={errors.name?.message}
          placeholder="e.g., Sales Data 2024"
          disabled={isUploading}
        />

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium mb-2">
            Description (optional)
          </label>
          <textarea
            id="description"
            {...register('description')}
            placeholder="Describe what this dataset contains..."
            rows={4}
            disabled={isUploading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          {errors.description && (
            <p className="text-red-600 text-sm mt-1">{errors.description.message}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/datasets')}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={!selectedFile || isUploading}
            className="flex-1"
          >
            {isUploading ? (
              <>
                <LoadingSpinner size="sm" variant="white" />
                <span className="ml-2">Uploading...</span>
              </>
            ) : (
              'Upload Dataset'
            )}
          </Button>
        </div>
      </form>

      {/* Help Text */}
      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h3 className="font-semibold mb-2">Requirements</h3>
        <ul className="text-sm text-gray-700 space-y-1 list-disc list-inside">
          <li>File must be in CSV format (.csv)</li>
          <li>Maximum file size: 5MB</li>
          <li>Maximum rows: 10,000</li>
          <li>Column names must start with a letter or underscore</li>
          <li>Column names can only contain letters, numbers, and underscores</li>
        </ul>
      </div>
    </div>
  );
}
