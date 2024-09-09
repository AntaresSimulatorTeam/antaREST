import { renderHook, act, waitFor } from "@testing-library/react";
import { vi, describe, expect, beforeEach } from "vitest";
import { useMatrix } from "./useMatrix";
import * as apiMatrix from "../../../services/api/matrix";
import * as apiStudy from "../../../services/api/study";
import {
  MatrixEditDTO,
  MatrixIndex,
  Operator,
  StudyOutputDownloadLevelDTO,
} from "../../../common/types";
import { MatrixData } from "./types";

vi.mock("../../../services/api/matrix");
vi.mock("../../../services/api/study");

describe("useMatrix", () => {
  const mockStudyId = "study123";
  const mockUrl = "https://studies/study123/matrix";

  const mockMatrixData: MatrixData = {
    data: [
      [1, 2],
      [3, 4],
    ],
    columns: [0, 1],
    index: [0, 1],
  };

  const mockMatrixIndex: MatrixIndex = {
    start_date: "2023-01-01",
    steps: 2,
    first_week_size: 7,
    level: StudyOutputDownloadLevelDTO.DAILY,
  };

  // Helper function to set up the hook and wait for initial loading
  const setupHook = async () => {
    vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
    vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(mockMatrixIndex);

    const { result } = renderHook(() =>
      useMatrix(mockStudyId, mockUrl, true, true),
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    return result;
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  test("should fetch matrix data and index on mount", async () => {
    vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
    vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(mockMatrixIndex);

    const result = await setupHook();

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockMatrixData.data);
    expect(result.current.columns.length).toBeGreaterThan(0);
    expect(result.current.dateTime.length).toBeGreaterThan(0);
  });

  test("should handle cell edit", async () => {
    vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
    vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(mockMatrixIndex);

    const result = await setupHook();

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleCellEdit([0, 1], 5);
    });

    expect(result.current.data[1][0]).toBe(5);
    expect(result.current.pendingUpdatesCount).toBe(1);
  });

  test("should handle multiple cells edit", async () => {
    vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
    vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(mockMatrixIndex);

    const result = await setupHook();

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleMultipleCellsEdit([
        { coordinates: [0, 1], value: 5 },
        { coordinates: [1, 0], value: 6 },
      ]);
    });

    expect(result.current.data[1][0]).toBe(5);
    expect(result.current.data[0][1]).toBe(6);
    expect(result.current.pendingUpdatesCount).toBe(2);
  });

  test("should handle save updates", async () => {
    vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
    vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(mockMatrixIndex);
    vi.mocked(apiMatrix.editMatrix).mockResolvedValue(undefined);

    const result = await setupHook();

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleCellEdit([0, 1], 5);
    });

    await act(async () => {
      await result.current.handleSaveUpdates();
    });

    const expectedEdit: MatrixEditDTO = {
      coordinates: [[1, 0]],
      operation: {
        operation: Operator.EQ,
        value: 5,
      },
    };

    expect(apiMatrix.editMatrix).toHaveBeenCalledWith(mockStudyId, mockUrl, [
      expectedEdit,
    ]);
    expect(result.current.pendingUpdatesCount).toBe(0);
  });

  test("should handle file import", async () => {
    const mockFile = new File([""], "test.csv", { type: "text/csv" });
    vi.mocked(apiStudy.importFile).mockResolvedValue("");
    vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
    vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(mockMatrixIndex);

    const result = await setupHook();

    await act(async () => {
      await result.current.handleImport(mockFile);
    });

    expect(apiStudy.importFile).toHaveBeenCalledWith(
      mockFile,
      mockStudyId,
      mockUrl,
    );
  });

  describe("Undo and Redo functionality", () => {
    test("should have correct initial undo/redo states", async () => {
      vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
      vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(
        mockMatrixIndex,
      );

      const result = await setupHook();

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.canUndo).toBe(false);
      expect(result.current.canRedo).toBe(false);
    });

    test("should update canUndo and canRedo states correctly after edits", async () => {
      vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
      vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(
        mockMatrixIndex,
      );

      const result = await setupHook();

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.handleCellEdit([0, 1], 5);
      });

      expect(result.current.canUndo).toBe(true);
      expect(result.current.canRedo).toBe(false);

      act(() => {
        result.current.undo();
      });

      expect(result.current.canUndo).toBe(false);
      expect(result.current.canRedo).toBe(true);

      act(() => {
        result.current.redo();
      });

      expect(result.current.canUndo).toBe(true);
      expect(result.current.canRedo).toBe(false);
    });

    test("should reset redo state after a new edit", async () => {
      vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
      vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(
        mockMatrixIndex,
      );

      const result = await setupHook();

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.handleCellEdit([0, 1], 5);
      });

      act(() => {
        result.current.undo();
      });

      expect(result.current.canRedo).toBe(true);

      act(() => {
        result.current.handleCellEdit([1, 0], 6);
      });

      expect(result.current.canUndo).toBe(true);
      expect(result.current.canRedo).toBe(false);
    });

    test("should handle undo to initial state", async () => {
      vi.mocked(apiStudy.getStudyData).mockResolvedValue(mockMatrixData);
      vi.mocked(apiMatrix.getStudyMatrixIndex).mockResolvedValue(
        mockMatrixIndex,
      );

      const result = await setupHook();

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      act(() => {
        result.current.handleCellEdit([0, 1], 5);
      });

      act(() => {
        result.current.undo();
      });

      expect(result.current.data).toEqual(mockMatrixData.data);
      expect(result.current.canUndo).toBe(false);
      expect(result.current.canRedo).toBe(true);
    });
  });
});
