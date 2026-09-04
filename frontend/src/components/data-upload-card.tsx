
import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import {
  FileUp,
  File,
  X,
  Check,
  FileSpreadsheet,
  Info
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/components/ui/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { v4 as uuidv4 } from 'uuid';
import type { User } from '@supabase/supabase-js';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined;
const REQUIRED_COLUMNS = ['Date', 'Channel', 'Spend', 'Conversions'];

interface DataFile {
  name: string;
  size: number;
  status: 'idle' | 'uploading' | 'success' | 'error';
  progress?: number;
  file?: File;
}

interface ColumnProfile {
  column: string;
  dtype: string;
  cardinality: number;
  missing_pct: number;
  std_dev: number | null;
}

interface ValidationResult {
  error: string | null;
  profile?: ColumnProfile[];
}

interface Props {
  onSuccess?: () => void;
  onViewDashboard?: () => void;
  onGenerateReport?: () => void;
}

export const DataUploadCard: React.FC<Props> = ({ onSuccess, onViewDashboard, onGenerateReport }) => {
  const [files, setFiles] = useState<DataFile[]>([]);
  const [user, setUser] = useState<User | null>(null);
  // Automated data profiling results (cardinality, missingness, std dev) per validated file —
  // the dashboard's data catalog for whatever was just uploaded.
  const [catalog, setCatalog] = useState<Record<string, ColumnProfile[]>>({});
  const { toast } = useToast();

  // Track the live Supabase auth session
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).map(file => ({
        name: file.name,
        size: file.size,
        status: 'idle' as const,
        file: file,
      }));
      
      setFiles(prevFiles => [...prevFiles, ...newFiles]);
    }
  };

  const handleRemoveFile = (index: number) => {
    setFiles(prevFiles => prevFiles.filter((_, i) => i !== index));
  };

  // Validate that an uploaded CSV matches the required marketing-spend schema, and (when the
  // backend is reachable) profile it — cardinality, missingness %, std dev per column — for
  // the data catalog. Falls back to a client-side header check (no profiling) if the API
  // isn't configured or isn't reachable.
  const validateCsvSchema = async (file: File): Promise<ValidationResult> => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      return { error: null };
    }

    if (API_BASE_URL) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/api/upload`, {
          method: 'POST',
          body: formData,
        });

        const body = await response.json().catch(() => null);

        if (!response.ok) {
          return { error: body?.detail || `Schema validation failed (HTTP ${response.status}).` };
        }

        return { error: null, profile: body?.profile };
      } catch (error) {
        console.warn('Schema validation API unreachable, falling back to a client-side header check:', error);
      }
    }

    const headerLine = (await file.slice(0, 4096).text()).split(/\r?\n/)[0] ?? '';
    const headers = headerLine.split(',').map((h) => h.trim());
    const missing = REQUIRED_COLUMNS.filter((col) => !headers.includes(col));
    if (missing.length > 0) {
      return {
        error: `CSV is missing required column(s): ${missing.join(', ')}. Expected schema: ${REQUIRED_COLUMNS.join(', ')}.`,
      };
    }
    return { error: null };
  };

  const handleUpload = async () => {
    // Check if user exists
    if (!user) {
      toast({
        title: "Authentication Required",
        description: "Please log in to upload data.",
        variant: "destructive"
      });
      return;
    }

    // Mark all files as uploading
    setFiles(prevFiles => 
      prevFiles.map(file => ({
        ...file,
        status: 'uploading',
        progress: 0
      }))
    );

    // Process each file
    for (let index = 0; index < files.length; index++) {
      const fileData = files[index];
      const file = fileData.file;
      
      if (!file) continue;

      try {
        // Validate schema (Date, Channel, Spend, Conversions) before uploading
        const { error: validationError, profile } = await validateCsvSchema(file);
        if (validationError) {
          setFiles(prevFiles =>
            prevFiles.map((f, i) => (i === index ? { ...f, status: 'error', progress: 0 } : f))
          );
          toast({
            title: 'Invalid file schema',
            description: validationError,
            variant: 'destructive'
          });
          continue;
        }
        if (profile) {
          setCatalog(prev => ({ ...prev, [file.name]: profile }));
        }

        // Set up progress tracking
        let progressInterval = setInterval(() => {
          setFiles(prevFiles => 
            prevFiles.map((f, i) => 
              i === index ? { 
                ...f, 
                progress: Math.min((f.progress || 0) + Math.random() * 10, 90) 
              } : f
            )
          );
        }, 200);

        // 1. Upload file to Supabase Storage with UUID
        const fileExt = file.name.split('.').pop();
        const fileName = `${uuidv4()}.${fileExt}`;
        const filePath = `user-files/${fileName}`;
        
        // Upload the file to Supabase Storage
        const { data: storageData, error: storageError } = await supabase.storage
          .from('csv_files')  // Changed from 'marketing_data' to 'csv_files'
          .upload(filePath, file, {
            cacheControl: '3600',
            upsert: false,
            contentType: file.type,
          });
          
        clearInterval(progressInterval);
        
        if (storageError) throw new Error(storageError.message);
        
        // Update progress to 95%
        setFiles(prevFiles => 
          prevFiles.map((f, i) => 
            i === index ? { ...f, progress: 95 } : f
          )
        );
        
        // 2. Create dataset entry in the database with all required fields
        const datasetInsert = {
          name: file.name,
          description: `Uploaded on ${new Date().toLocaleString()}`,
          file_path: filePath,
          file_size: file.size,
          file_type: file.type,
        };
        
        // Add owner_id from the authenticated user
        if (user?.id) {
          Object.assign(datasetInsert, { owner_id: user.id });
        }
        
        const { data: datasetData, error: datasetError } = await supabase
          .from('datasets')
          .insert(datasetInsert)
          .select()
          .single();
          
        if (datasetError) throw new Error(datasetError.message);
        
        // Update progress to 100% and mark as success
        setFiles(prevFiles => 
          prevFiles.map((f, i) => 
            i === index ? { ...f, status: 'success', progress: 100 } : f
          )
        );
      } catch (error) {
        console.error('Error uploading file:', error);
        
        // Mark file as error
        setFiles(prevFiles => 
          prevFiles.map((f, i) => 
            i === index ? { ...f, status: 'error', progress: 0 } : f
          )
        );
        
        toast({
          title: "Upload failed",
          description: error instanceof Error ? error.message : `Failed to upload ${file.name}. Please try again.`,
          variant: "destructive"
        });
      }
    }

    // Check if all files are uploaded successfully
    const allUploaded = files.every(file => file.status === 'success');
    if (allUploaded) {
      toast({
        title: "Upload complete",
        description: "All files have been successfully uploaded.",
      });

      // Call onSuccess callback if provided
      if (onSuccess) {
        onSuccess();
      }
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const allFilesUploaded = files.length > 0 && files.every(file => file.status === 'success');

  // In the return statement, update the CardFooter:
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-xl">Upload Your Data</CardTitle>
        <CardDescription>
          Upload your marketing data files to generate insights
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>Required CSV schema</AlertTitle>
          <AlertDescription>
            Marketing spend CSVs must include these columns: <strong>Date</strong>, <strong>Channel</strong>,{' '}
            <strong>Spend</strong>, and <strong>Conversions</strong>. Extra columns are fine — these four are
            the minimum required for analysis.
          </AlertDescription>
        </Alert>

        <div
          className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => document.getElementById('file-upload')?.click()}
        >
          <FileUp className="h-10 w-10 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm font-medium">Drag & drop your files here or click to browse</p>
          <p className="text-xs text-muted-foreground mt-1">
            Supported formats: CSV, Excel, and text files
          </p>
          <input 
            id="file-upload" 
            type="file" 
            multiple 
            accept=".csv,.xlsx,.xls,.txt" 
            className="hidden" 
            onChange={handleFileChange}
          />
        </div>
        
        {files.length > 0 && (
          <div className="space-y-2 mt-4">
            <p className="text-sm font-medium">Files ({files.length})</p>
            <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
              {files.map((file, index) => (
                <div 
                  key={index} 
                  className="flex items-center justify-between p-2 rounded-md bg-muted/50"
                >
                  <div className="flex items-center">
                    <FileSpreadsheet className="h-5 w-5 text-marketing-primary mr-2" />
                    <div>
                      <p className="text-sm font-medium truncate max-w-[180px]">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center">
                    {file.status === 'uploading' && (
                      <div className="w-20 h-1 bg-muted rounded-full overflow-hidden mr-2">
                        <div 
                          className="h-full bg-marketing-primary" 
                          style={{ width: `${file.progress}%` }}
                        ></div>
                      </div>
                    )}
                    
                    {file.status === 'success' ? (
                      <Check className="h-5 w-5 text-green-500" />
                    ) : file.status === 'error' ? (
                      <X className="h-5 w-5 text-destructive" />
                    ) : (
                      <button 
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveFile(index);
                        }}
                        className="h-5 w-5 text-muted-foreground hover:text-destructive"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {Object.entries(catalog).map(([fileName, profile]) => (
          <div key={fileName} className="space-y-2">
            <p className="text-sm font-medium">Data catalog — {fileName}</p>
            <div className="overflow-x-auto rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Column</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Cardinality</TableHead>
                    <TableHead>Missing %</TableHead>
                    <TableHead>Std Dev</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {profile.map((col) => (
                    <TableRow key={col.column}>
                      <TableCell className="font-medium">{col.column}</TableCell>
                      <TableCell>{col.dtype}</TableCell>
                      <TableCell>{col.cardinality}</TableCell>
                      <TableCell>{col.missing_pct.toFixed(1)}%</TableCell>
                      <TableCell>{col.std_dev !== null ? col.std_dev.toLocaleString() : '—'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        ))}
      </CardContent>
      
      <CardFooter className="flex flex-wrap gap-2 justify-between">
        <Button
          variant="outline"
          onClick={() => { setFiles([]); setCatalog({}); }}
          disabled={files.length === 0}
        >
          Clear All
        </Button>
        
        <div className="flex flex-wrap gap-2">
          {allFilesUploaded && onViewDashboard && (
            <Button 
              onClick={onViewDashboard}
              variant="default"
            >
              View Dashboard
            </Button>
          )}
          
          {allFilesUploaded && onGenerateReport && (
            <Button 
              onClick={onGenerateReport}
              variant="outline"
            >
              Generate Report
            </Button>
          )}
          
          {!allFilesUploaded && (
            <Button 
              onClick={handleUpload} 
              disabled={files.length === 0 || allFilesUploaded}
            >
              {allFilesUploaded ? 'Uploaded' : 'Upload Files'}
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
};
