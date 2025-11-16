import { api } from '@/services/api';
import type { BulkImportResponse } from '@/types';

/**
 * Student service for teacher operations
 * Handles student export and bulk import
 */
export const studentService = {
  /**
   * Export all students as CSV file
   * Downloads CSV with student data (name, email, points, completion, last_active)
   */
  async exportStudents(): Promise<void> {
    try {
      const response = await api.get('export/students');
      const blob = await response.blob();

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `students_export_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
      throw error;
    }
  },

  /**
   * Import students from CSV file
   * @param file - CSV file with columns: email, name
   * @returns Import results with generated passwords
   */
  async importStudents(file: File): Promise<BulkImportResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('import/students', {
      body: formData,
    }).json<BulkImportResponse>();

    return response;
  },
};
