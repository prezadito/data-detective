import { useState } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { studentService } from '@/services/studentService';
import { showSuccessToast, showErrorToast } from '@/utils/toast';
import type { BulkImportResponse } from '@/types';

export interface ImportModalProps {
  /**
   * Whether the modal is open
   */
  isOpen: boolean;

  /**
   * Callback when modal should close
   */
  onClose: () => void;

  /**
   * Callback after successful import (to refresh student list)
   */
  onImportSuccess: () => void;
}

/**
 * ImportModal component - Multi-step student CSV import flow
 *
 * Three states:
 * 1. File Selection - Choose CSV file
 * 2. Uploading - Show progress
 * 3. Results - Display import results, passwords, and errors
 */
export function ImportModal({ isOpen, onClose, onImportSuccess }: ImportModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [results, setResults] = useState<BulkImportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showErrors, setShowErrors] = useState(false);

  // Reset state when modal closes
  const handleClose = () => {
    setSelectedFile(null);
    setIsUploading(false);
    setResults(null);
    setError(null);
    setShowErrors(false);
    onClose();
  };

  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      setError('Please select a CSV file');
      setSelectedFile(null);
      return;
    }

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File is too large. Maximum size is 5MB');
      setSelectedFile(null);
      return;
    }

    setError(null);
    setSelectedFile(file);
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      setIsUploading(true);
      setError(null);

      const response = await studentService.importStudents(selectedFile);
      setResults(response);

      // Show success toast
      if (response.successful > 0) {
        showSuccessToast(
          `${response.successful} student${response.successful !== 1 ? 's' : ''} imported successfully`
        );
      }
    } catch (err: any) {
      setError(err.message || 'Failed to import students');
      showErrorToast('Import failed. Please check your file and try again.');
    } finally {
      setIsUploading(false);
    }
  };

  // Handle "Done" button - close modal and refresh list
  const handleDone = () => {
    if (results && results.successful > 0) {
      onImportSuccess();
    }
    handleClose();
  };

  // Handle "Import More" - reset to file selection
  const handleImportMore = () => {
    setSelectedFile(null);
    setResults(null);
    setError(null);
    setShowErrors(false);
  };

  // Copy all passwords to clipboard
  const handleCopyPasswords = async () => {
    if (!results || results.imported_students.length === 0) return;

    const text = results.imported_students
      .map((s) => `${s.email}: ${s.temporary_password}`)
      .join('\n');

    try {
      await navigator.clipboard.writeText(text);
      showSuccessToast('Passwords copied to clipboard');
    } catch (err) {
      showErrorToast('Failed to copy passwords');
    }
  };

  // Download passwords as CSV
  const handleDownloadPasswords = () => {
    if (!results || results.imported_students.length === 0) return;

    const csvContent = [
      'email,name,temporary_password',
      ...results.imported_students.map(
        (s) => `${s.email},${s.name},${s.temporary_password}`
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `student_passwords_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    showSuccessToast('Passwords downloaded');
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Import Students" size="lg">
      {/* STATE 1: FILE SELECTION */}
      {!isUploading && !results && (
        <div className="space-y-6">
          {/* Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">CSV File Requirements</h3>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>File must have columns: <code className="bg-blue-100 px-1 rounded">email</code> and <code className="bg-blue-100 px-1 rounded">name</code></li>
              <li>Maximum file size: 5MB</li>
              <li>Duplicate emails will be skipped</li>
              <li>Temporary passwords will be generated automatically</li>
            </ul>
          </div>

          {/* File Upload Area */}
          <div>
            <label className="block text-sm font-medium mb-2">
              Select CSV File
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileSelect}
                className="hidden"
                id="import-file-upload"
              />
              <label htmlFor="import-file-upload" className="cursor-pointer">
                {selectedFile ? (
                  <div>
                    <div className="text-green-600 text-4xl mb-2">📄</div>
                    <p className="font-medium text-gray-900">{selectedFile.name}</p>
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
                    <p className="text-gray-600">Click to select a CSV file</p>
                    <p className="text-sm text-gray-500 mt-1">
                      Or drag and drop your file here
                    </p>
                  </div>
                )}
              </label>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleUpload}
              disabled={!selectedFile}
            >
              Upload & Import
            </Button>
          </div>
        </div>
      )}

      {/* STATE 2: UPLOADING */}
      {isUploading && (
        <div className="py-12 text-center">
          <LoadingSpinner size="lg" />
          <p className="text-gray-600 mt-4 font-medium">
            Uploading and importing students...
          </p>
          {selectedFile && (
            <p className="text-sm text-gray-500 mt-2">{selectedFile.name}</p>
          )}
        </div>
      )}

      {/* STATE 3: RESULTS */}
      {!isUploading && results && (
        <div className="space-y-6">
          {/* Summary Statistics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-900">
                {results.successful}
              </div>
              <div className="text-sm text-green-700 mt-1">Imported</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-yellow-900">
                {results.skipped}
              </div>
              <div className="text-sm text-yellow-700 mt-1">Skipped</div>
            </div>
            <div className="bg-red-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-red-900">
                {results.failed}
              </div>
              <div className="text-sm text-red-700 mt-1">Failed</div>
            </div>
          </div>

          {/* Passwords Section */}
          {results.imported_students.length > 0 && (
            <div className="border border-yellow-300 bg-yellow-50 rounded-lg p-4">
              <div className="flex items-start mb-3">
                <span className="text-yellow-600 text-xl mr-2">⚠️</span>
                <div>
                  <h3 className="font-semibold text-yellow-900">
                    Temporary Passwords Generated
                  </h3>
                  <p className="text-sm text-yellow-800 mt-1">
                    Save these passwords securely. They won't be shown again.
                  </p>
                </div>
              </div>

              {/* Passwords Table */}
              <div className="bg-white rounded border border-yellow-200 overflow-hidden max-h-60 overflow-y-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Email
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Name
                      </th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                        Password
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {results.imported_students.map((student, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-gray-900">{student.email}</td>
                        <td className="px-3 py-2 text-gray-900">{student.name}</td>
                        <td className="px-3 py-2 font-mono text-sm text-gray-900">
                          {student.temporary_password}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Password Actions */}
              <div className="flex gap-2 mt-3">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopyPasswords}
                >
                  📋 Copy All Passwords
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleDownloadPasswords}
                >
                  📥 Download as CSV
                </Button>
              </div>
            </div>
          )}

          {/* Errors Section */}
          {results.errors.length > 0 && (
            <div className="border border-red-300 bg-red-50 rounded-lg p-4">
              <button
                onClick={() => setShowErrors(!showErrors)}
                className="flex items-center justify-between w-full text-left"
              >
                <div className="flex items-center">
                  <span className="text-red-600 text-xl mr-2">✗</span>
                  <h3 className="font-semibold text-red-900">
                    {results.errors.length} Error{results.errors.length !== 1 ? 's' : ''}
                  </h3>
                </div>
                <span className="text-red-600">
                  {showErrors ? '▼' : '▶'}
                </span>
              </button>

              {showErrors && (
                <div className="mt-3 bg-white rounded border border-red-200 overflow-hidden max-h-60 overflow-y-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                          Row
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                          Email
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase">
                          Error
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {results.errors.map((err, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-3 py-2 text-gray-900">{err.row_number}</td>
                          <td className="px-3 py-2 text-gray-900">
                            {err.email || 'N/A'}
                          </td>
                          <td className="px-3 py-2 text-red-700">{err.error}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={handleImportMore}>
              Import More Students
            </Button>
            <Button variant="primary" onClick={handleDone}>
              Done
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}

ImportModal.displayName = 'ImportModal';
