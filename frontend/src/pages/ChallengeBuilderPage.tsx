import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { customChallengeService } from '@/services/customChallengeService';
import { datasetService } from '@/services/datasetService';
import type { DatasetListItem, CustomChallengeResponse } from '@/types';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const challengeSchema = z.object({
  dataset_id: z.number().min(1, 'Please select a dataset'),
  title: z.string().min(1, 'Title is required').max(200, 'Title too long'),
  description: z.string().min(1, 'Description is required').max(2000, 'Description too long'),
  points: z.number().min(50, 'Minimum 50 points').max(500, 'Maximum 500 points'),
  difficulty: z.enum(['easy', 'medium', 'hard']),
  expected_query: z.string().min(1, 'SQL query is required').max(5000, 'Query too long'),
  hint1: z.string().min(10, 'Hint must be at least 10 characters').max(200, 'Hint too long'),
  hint2: z.string().min(10, 'Hint must be at least 10 characters').max(200, 'Hint too long'),
  hint3: z.string().min(10, 'Hint must be at least 10 characters').max(200, 'Hint too long'),
});

type ChallengeFormData = z.infer<typeof challengeSchema>;

export function ChallengeBuilderPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedDatasetId = searchParams.get('dataset');

  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [isLoadingDatasets, setIsLoadingDatasets] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createdChallenge, setCreatedChallenge] = useState<CustomChallengeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue,
  } = useForm<ChallengeFormData>({
    resolver: zodResolver(challengeSchema),
    mode: 'onBlur',
    defaultValues: {
      points: 100,
      difficulty: 'medium',
      dataset_id: preselectedDatasetId ? parseInt(preselectedDatasetId) : undefined,
    },
  });

  const selectedDatasetId = watch('dataset_id');

  useEffect(() => {
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      setIsLoadingDatasets(true);
      const response = await datasetService.getDatasets();
      setDatasets(response.datasets);

      // If preselected dataset, set it
      if (preselectedDatasetId && response.datasets.length > 0) {
        setValue('dataset_id', parseInt(preselectedDatasetId));
      }
    } catch (err) {
      console.error('Failed to load datasets:', err);
      setError('Failed to load datasets');
    } finally {
      setIsLoadingDatasets(false);
    }
  };

  const onSubmit = async (data: ChallengeFormData) => {
    try {
      setIsSubmitting(true);
      setError(null);

      const challenge = await customChallengeService.createChallenge({
        dataset_id: data.dataset_id,
        title: data.title,
        description: data.description,
        points: data.points,
        difficulty: data.difficulty,
        expected_query: data.expected_query,
        hints: [data.hint1, data.hint2, data.hint3],
      });

      setCreatedChallenge(challenge);
    } catch (err: any) {
      setError(err.message || 'Failed to create challenge');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Show success screen after creation
  if (createdChallenge) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
          <div className="text-green-600 text-5xl mb-4">✓</div>
          <h2 className="text-2xl font-bold mb-2">Challenge Created Successfully!</h2>
          <p className="text-gray-600 mb-6">
            {createdChallenge.title} - {createdChallenge.points} points
          </p>

          <div className="bg-white border rounded-lg p-4 mb-6 text-left">
            <h3 className="font-semibold mb-2">Challenge Details</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Dataset:</span>
                <span className="font-medium">{createdChallenge.dataset_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Difficulty:</span>
                <span className="font-medium capitalize">{createdChallenge.difficulty}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Points:</span>
                <span className="font-medium">{createdChallenge.points}</span>
              </div>
            </div>
          </div>

          <div className="flex gap-4 justify-center">
            <Button onClick={() => navigate('/challenges/custom')}>
              View All Challenges
            </Button>
            <Button
              variant="primary"
              onClick={() => window.location.reload()}
            >
              Create Another
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (isLoadingDatasets) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (datasets.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="text-center py-12 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 className="text-lg font-semibold mb-2">No Datasets Available</h3>
          <p className="text-gray-600 mb-4">
            You need to upload a dataset before creating challenges
          </p>
          <Button onClick={() => navigate('/datasets/upload')}>
            Upload Dataset
          </Button>
        </div>
      </div>
    );
  }

  const selectedDataset = datasets.find(d => d.id === selectedDatasetId);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Create Custom Challenge</h1>
        <p className="text-gray-600">
          Build a SQL challenge for students using your uploaded datasets
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Dataset Selection */}
        <div>
          <label htmlFor="dataset_id" className="block text-sm font-medium mb-2">
            Dataset *
          </label>
          <select
            id="dataset_id"
            {...register('dataset_id', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSubmitting}
          >
            <option value="">Select a dataset...</option>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.name} ({dataset.row_count} rows)
              </option>
            ))}
          </select>
          {errors.dataset_id && (
            <p className="text-red-600 text-sm mt-1">{errors.dataset_id.message}</p>
          )}
          {selectedDataset && (
            <p className="text-sm text-gray-600 mt-2">
              Table: <code className="bg-gray-100 px-2 py-1 rounded">{selectedDataset.table_name}</code>
            </p>
          )}
        </div>

        {/* Title */}
        <Input
          label="Challenge Title *"
          {...register('title')}
          error={errors.title?.message}
          placeholder="e.g., Find Top 5 Products by Revenue"
          disabled={isSubmitting}
        />

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium mb-2">
            Description *
          </label>
          <textarea
            id="description"
            {...register('description')}
            placeholder="Describe what students need to do..."
            rows={4}
            disabled={isSubmitting}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          {errors.description && (
            <p className="text-red-600 text-sm mt-1">{errors.description.message}</p>
          )}
        </div>

        {/* Difficulty and Points */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="difficulty" className="block text-sm font-medium mb-2">
              Difficulty *
            </label>
            <select
              id="difficulty"
              {...register('difficulty')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isSubmitting}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
            {errors.difficulty && (
              <p className="text-red-600 text-sm mt-1">{errors.difficulty.message}</p>
            )}
          </div>

          <Input
            label="Points (50-500) *"
            type="number"
            {...register('points', { valueAsNumber: true })}
            error={errors.points?.message}
            disabled={isSubmitting}
          />
        </div>

        {/* Expected Query */}
        <div>
          <label htmlFor="expected_query" className="block text-sm font-medium mb-2">
            Expected SQL Query *
          </label>
          <textarea
            id="expected_query"
            {...register('expected_query')}
            placeholder={`SELECT * FROM ${selectedDataset?.table_name || 'your_table'} WHERE ...`}
            rows={6}
            disabled={isSubmitting}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm disabled:bg-gray-100"
          />
          {errors.expected_query && (
            <p className="text-red-600 text-sm mt-1">{errors.expected_query.message}</p>
          )}
          <p className="text-sm text-gray-600 mt-1">
            This query will be executed to validate student submissions
          </p>
        </div>

        {/* Hints */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h3 className="font-semibold mb-4">Hints (3 required)</h3>
          <div className="space-y-4">
            <Input
              label="Hint 1 (Easiest) *"
              {...register('hint1')}
              error={errors.hint1?.message}
              placeholder="e.g., Use the WHERE clause to filter results"
              disabled={isSubmitting}
            />
            <Input
              label="Hint 2 *"
              {...register('hint2')}
              error={errors.hint2?.message}
              placeholder="e.g., Consider using the > operator"
              disabled={isSubmitting}
            />
            <Input
              label="Hint 3 (Most helpful) *"
              {...register('hint3')}
              error={errors.hint3?.message}
              placeholder="e.g., Try: SELECT * FROM table WHERE column > value"
              disabled={isSubmitting}
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4 pt-4 border-t">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/challenges/custom')}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isSubmitting}
            className="flex-1"
          >
            {isSubmitting ? (
              <>
                <LoadingSpinner size="sm" variant="white" />
                <span className="ml-2">Creating Challenge...</span>
              </>
            ) : (
              'Create Challenge'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
