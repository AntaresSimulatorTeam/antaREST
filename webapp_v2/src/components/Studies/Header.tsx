import React from 'react';
import { styled } from '@mui/material/styles';
import TravelExploreOutlinedIcon from '@mui/icons-material/TravelExploreOutlined';
import GetAppOutlinedIcon from '@mui/icons-material/GetAppOutlined';
import AddCircleOutlineOutlinedIcon from '@mui/icons-material/AddCircleOutlineOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import TextField from '@mui/material/TextField';
import { useTranslation } from 'react-i18next';
import { Box, Button, Divider, InputAdornment, Typography } from '@mui/material';

const Root = styled('div')(({ theme }) => ({
  width: '100%',
  height: 'auto',
  display: 'flex',
  flexFlow: 'column nowrap',
  justifyContent: 'flex-start',
  alignItems: 'center',
  padding: theme.spacing(2, 0),
  boxSizing: 'border-box',
}));

const Searchbar = styled(TextField)(({ theme }) => ({
  color: theme.palette.grey[400],
  width: '300px',

  "& .MuiOutlinedInput-root": {
    backgroundColor: theme.palette.primary.dark,
    border: `1px solid ${theme.palette.grey[400]}`,
    height: '40px',
    "&.Mui-focused fieldset": {
      color: theme.palette.grey[400],
      border: `1px solid ${theme.palette.grey[400]}`,
    }
  }
}));

interface Props {
    inputValue: string;
    setInputValue: (value: string) => void;
    onImportClick: () => void;
    onCreateClick: () => void;
    onFilterClick: () => void;
}

function Header(props: Props) {
    const [t] = useTranslation();
    const { inputValue, setInputValue, onImportClick, onCreateClick, onFilterClick } = props;
  return (
    <Root>
        <Box width="100%" alignItems="center" display="flex" px={3}>
            <Box alignItems="center" display="flex">
                <TravelExploreOutlinedIcon sx={{ color: "grey.400", w: '64px', h: '64px' }} />
                <Typography color='white' sx={{ ml: 2, fontSize: '1.8em' }}>{t('main:studies')}</Typography>
            </Box>
            <Box alignItems="center" justifyContent="flex-end" flexGrow={1} display="flex">
                <Button variant="outlined" color="secondary" startIcon={<GetAppOutlinedIcon />} onClick={onImportClick}>
                    {t('main:import')}
                </Button>
                <Button sx={{ m: 2 }} variant="contained" color="secondary" startIcon={<AddCircleOutlineOutlinedIcon />} onClick={onCreateClick}>
                    {t('main:create')}
                </Button>
            </Box>
        </Box>
        <Box display="flex" width="100%" alignItems="center" px={3}>
            <Box display="flex" width="100%" alignItems="center">
                <Searchbar
                    id="standard-basic"
                    placeholder={t('main:search')}
                    value={inputValue}
                    onChange={(event) => setInputValue(event.target.value as string)}
                    InputLabelProps={{
                        sx: { color: 'grey.400' },
                    }}
                    InputProps={{
                        startAdornment: (
                        <InputAdornment position="start">
                            <SearchOutlinedIcon sx={{ color: 'grey.400' }} />
                        </InputAdornment>
                        ),
                        sx: { color: 'grey.400' } }}/>
                <Divider style={{ width: '1px', height: '40px', backgroundColor: 'gray', margin: '0px 16px' }}/>
                <Button sx={{color:'primary.light', borderStyle: "solid",  borderColor: 'primary.light' }} variant="outlined" onClick={onFilterClick}>
                    {t('main:filter')}
                </Button>
            </Box>
        </Box>
    </Root>   
  );
}

export default Header;
