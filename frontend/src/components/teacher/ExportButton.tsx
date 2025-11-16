import { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { studentService } from '@/services/studentService';
import { showSuccessToast, showApiErrorToast } from '@/utils/toast';

export interface ExportButtonProps {
  /**
   * Button variant
   * @default 'outline'
   */
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';

  /**
   * Button size
   * @default 'md'
   */
  size?: 'sm' | 'md' | 'lg';
}

/**
 * ExportButton component - Exports student list as CSV
 *
 * Triggers CSV download with student data:
 * - name
 * - email
 * - total_points
 * - completion_percentage
 * - last_active
 */
export function ExportButton({ variant = 'outline', size = 'md' }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    try {
      setIsExporting(true);
      await studentService.exportStudents();
      showSuccessToast('Student data exported successfully');
    } catch (error) {
      await showApiErrorToast(error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Button
      onClick={handleExport}
      variant={variant}
      size={size}
      isLoading={isExporting}
      disabled={isExporting}
    >
      {!isExporting && (
        <span className="mr-2" aria-hidden="true">
          📥
        </span>
      )}
      Export CSV
    </Button>
  );
}

ExportButton.displayName = 'ExportButton';
