package org.iara.campo

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ChatBubbleOutline
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import org.iara.campo.ui.CampoViewModel
import org.iara.campo.ui.Cores
import org.iara.campo.ui.IaraTema
import org.iara.campo.ui.TelaAjustes
import org.iara.campo.ui.TelaCampo
import org.iara.campo.ui.TelaRegistros

class MainActivity : ComponentActivity() {
    private val vm: CampoViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            IaraTema {
                var aba by rememberSaveable { mutableIntStateOf(0) }
                val abas = listOf(
                    Icons.Outlined.ChatBubbleOutline to "Campo",
                    Icons.Outlined.Description to "Registros",
                    Icons.Outlined.Tune to "Ajustes",
                )
                Scaffold(
                    containerColor = Cores.Palha,
                    bottomBar = {
                        NavigationBar(containerColor = Cores.Papel) {
                            abas.forEachIndexed { i, (icone, nome) ->
                                NavigationBarItem(
                                    selected = aba == i,
                                    onClick = { aba = i },
                                    icon = { Icon(icone, contentDescription = null) },
                                    label = { Text(nome) },
                                    colors = NavigationBarItemDefaults.colors(
                                        selectedIconColor = Cores.VerdeCopaiba,
                                        selectedTextColor = Cores.VerdeCopaiba,
                                        indicatorColor = Cores.VerdeClaro,
                                        unselectedIconColor = Cores.Texto2,
                                        unselectedTextColor = Cores.Texto2,
                                    ),
                                )
                            }
                        }
                    },
                ) { espaco ->
                    Column(Modifier.fillMaxSize().padding(espaco).imePadding()) {
                        when (aba) {
                            0 -> TelaCampo(vm)
                            1 -> TelaRegistros(vm)
                            else -> TelaAjustes(vm)
                        }
                    }
                }
            }
        }
    }
}
