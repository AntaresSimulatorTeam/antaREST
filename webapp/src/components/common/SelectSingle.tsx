import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  SxProps,
  Theme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { GenericInfo } from "../../common/types";

interface Props {
  name: string;
  label?: string;
  list: Array<GenericInfo>;
  data: string | undefined;
  setValue?: (data: string) => void;
  sx?: SxProps<Theme> | undefined;
  optional?: boolean;
  variant?: "filled" | "standard" | "outlined" | undefined;
  handleChange?: (key: string, value: string | number) => void;
  required?: boolean;
}

function SelectSingle(props: Props) {
  const {
    name,
    label = name,
    list,
    data,
    setValue,
    sx,
    variant,
    optional,
    handleChange,
    required,
  } = props;
  const [t] = useTranslation();

  const basicHandleChange = (event: SelectChangeEvent<string>) => {
    const {
      target: { value },
    } = event;
    if (setValue) {
      setValue(value);
    }
  };

  return (
    <FormControl
      variant={variant}
      sx={
        variant === "filled"
          ? {
              ...sx,
              ".Mui-focused": { backgroundColor: "rgba(255, 255, 255, 0.09)" },
              ".MuiInputLabel-root": { backgroundColor: "unset" },
            }
          : sx
      }
      required={required}
    >
      <InputLabel
        id={`single-checkbox-label-${name}`}
        sx={{ color: "rgba(255, 255, 255, 0.7)" }}
      >
        {label}
      </InputLabel>
      <Select
        labelId={`single-checkbox-label-${name}`}
        id={`single-checkbox-${name}`}
        value={data}
        label={label}
        onChange={
          handleChange
            ? (e) => handleChange(name, e.target.value as string)
            : basicHandleChange
        }
        sx={
          variant === "filled"
            ? {
                background: "rgba(255, 255, 255, 0.09)",
                borderBottom: "1px solid rgba(255, 255, 255, 0.42)",
                ".MuiSelect-icon": {
                  backgroundColor: "#222333",
                },
                "&:focus": {
                  backgroundColor: "rgba(255, 255, 255, 0.09) !important",
                },
                "&:hover": {
                  backgroundColor: "rgba(255, 255, 255, 0.09)",
                },
              }
            : {}
        }
      >
        {optional && (
          <MenuItem value="" key="None">
            {t("global:global.none")}
          </MenuItem>
        )}
        {list.map(({ id, name }) => (
          <MenuItem key={id} value={id}>
            {name}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

SelectSingle.defaultProps = {
  sx: { m: 0, width: 200 },
  variant: "filled",
  label: undefined,
  optional: false,
  setValue: undefined,
  handleChange: undefined,
  required: false,
};

export default SelectSingle;
