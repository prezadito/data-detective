/**
 * Dataset service - API calls for dataset upload and management
 */

import { api } from './api';
import type {
  DatasetResponse,
  DatasetListResponse,
  DatasetDetailResponse,
} from '@/types';

export const datasetService = {
  /**
   * Upload a CSV file and create a dataset
   * @param file - CSV file to upload
   * @param name - Dataset name
   * @param description - Optional description
   * @returns Created dataset
   */
  async uploadDataset(
    file: File,
    name: string,
    description?: string
  ): Promise<DatasetResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    if (description) {
      formData.append('description', description);
    }

    return await api
      .post('datasets/upload', {
        body: formData,
      })
      .json<DatasetResponse>();
  },

  /**
   * Get list of datasets for current teacher
   * @param offset - Pagination offset
   * @param limit - Pagination limit
   * @returns List of datasets
   */
  async getDatasets(
    offset: number = 0,
    limit: number = 50
  ): Promise<DatasetListResponse> {
    return await api
      .get('datasets', {
        searchParams: { offset, limit },
      })
      .json<DatasetListResponse>();
  },

  /**
   * Get detailed dataset information including sample data
   * @param datasetId - Dataset ID
   * @returns Dataset details with schema and sample data
   */
  async getDatasetDetail(datasetId: number): Promise<DatasetDetailResponse> {
    return await api.get(`datasets/${datasetId}`).json<DatasetDetailResponse>();
  },

  /**
   * Delete a dataset and its associated table
   * @param datasetId - Dataset ID
   * @returns Success message
   */
  async deleteDataset(datasetId: number): Promise<{ message: string }> {
    return await api.delete(`datasets/${datasetId}`).json();
  },
};
